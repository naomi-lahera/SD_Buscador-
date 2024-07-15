from node.chord.chord import ChordNode, ChordNodeReference
import threading
import socket
from typing import List
import os
import sqlite3
from logic.models.model_interface import ModelSearchInterface
from data_access_layer.controller_interface import BaseController
import logging
import hashlib
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController
from queue import Queue

# Configuración inicial de logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)

# Códigos de operación
FIND_SUCCESSOR = 1
FIND_PREDECESSOR = 2
GET_SUCCESSOR = 3
GET_PREDECESSOR = 4
NOTIFY = 5
INSERT_NODE = 6
REMOVE_NODE = 7
JOIN = 8
ELECTION = 9
ELECTION_OK = 10
ELECTION_WINNER = 11
CHECK_PREDECESSOR = 12
CLOSEST_PRECEDING_FINGER = 13
STORE_KEY = 14
RETRIEVE_KEY = 15
SEARCH = 16
REQUEST_BROADCAST_QUERY = 17
FIND_LEADER = 18
PING = 19
QUERY_FROM_CLIENT = 20
def read_or_create_db(ip):
    ip = str(ip)
    folder_path = 'src/server/data/nodes_data/'
    full_path = os.path.join(folder_path, ip)
    
    if os.path.exists(f"{full_path}/database.db"):
        logger.debug("El nodo ya existia")
        return 
    
    else:
        # os.makedirs(full_path)
        # logger.debug(f"Carpeta creada en: {full_path}")
        try:
            conexion = sqlite3.connect(os.path.join(full_path, 'database.db'))
            logger.debug("Conexión a la base de datos exitosa")
        except Exception as e:
            logger.debug(f"Error al conectar a la base de datos: {e}")
            return
    
        cursor = conexion.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
        	id INTEGER PRIMARY KEY,
        	texto_documento TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS replica_succ (
        	id INTEGER PRIMARY KEY,
        	texto_documento TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS replica_pred (
        	id INTEGER PRIMARY KEY,
        	texto_documento TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        conexion.commit()
        conexion.close()
        logger.debug("La base de datos se creó correctamente")    

class Node(ChordNode):
    responses_queue = Queue()
    query_states = {}
    query_states_lock = threading.Lock()

    def __init__(self, model: ModelSearchInterface, controller: BaseController, ip: str, port: int = 8001, m: int = 160, leader_ip='172.17.0.2', leader_port=8002):
        read_or_create_db(ip)
        super().__init__(ip, port, m)
        self.logger = logging.getLogger(__name__)
        self.controller = controller
        self.model = model
        self.data = {}
        self.is_leader = False
        self.leader_ip = leader_ip
        self.leader_port = leader_port
        threading.Thread(target=self.start_server, daemon=True).start()  # Iniciar servidor
        threading.Thread(target=self._receiver_broadcast, daemon=True).start()
        threading.Thread(target=self.stabilize, daemon=True).start()
        if self.ip == self.leader_ip:
            self.is_leader = True
            threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
        logger.debug(self.ip)

    def add_doc(self,document):
        return self.controller.create_document(document)
    
    def upd_doc(self,id,text):
        return self.controller.update_document(id,text)
    
    def del_doc(self,id):
        return self.controller.delete_document(id)
    
    def get_docs(self):
        return self.controller.get_documents()
    
    def get_doc_by_id(self,id):
        return self.controller.get_document_by_id(id)
    
    def search(self, query) -> List:
        return self.model.retrieve(query,self.controller)

    def listen_for_broadcast(self):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.debug(f"listen : {('', self.port+1)}")
        broadcast_socket.bind(('', self.port+1))
        while True:
            msg, client_address = broadcast_socket.recvfrom(1024)
            logger.debug(f"Broadcast recibido de {client_address}: {msg.decode('utf-8')}")
            logger.debug("\n****************************************")
            logger.debug(f"\nMensaje del cliente: {msg.decode('utf-8').split(',')}")
            logger.debug("\n****************************************")
            option, ip_client,text = msg.decode('utf-8').split(',')
            option = int(option)
            
            if option == QUERY_FROM_CLIENT:
                print("query")
                client_to_send ,documents = self.receive_query_from_client(self,text,ip_client)
                response = f'{documents}'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (client_to_send,8004))  # Envía la respuesta al cliente
                print(f"{documents} sended to {(client_to_send,8004)}")
                
            elif option == FIND_LEADER:
                print("finding leader")
                response = f'{self.ip},{self.port}'.encode()  # Prepara la respuesta con IP y puerto del líder
                logger.debug(f"enviando respuesta {response} a {(ip_client,8003)}")
                broadcast_socket.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente

    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        logger.debug(f"Solicitud recibida: {request}")
        client_socket.sendall(b"Solicitud recibida")
        client_socket.close()

    def receive_query_from_client(self, chord_node, query: str, ip_client: str):
        hashed_query = hashlib.sha256(query.encode()).hexdigest()
        with Node.query_states_lock:
            if hashed_query not in Node.query_states:
                Node.query_states[hashed_query] = {
                    "responses_list": [],
                    "timeout_timer": None,
                    "query": query
                }
        data_to_send = f'{hashed_query},{query}'
        chord_node._send_broadcast(17, data_to_send)
        wait_time = 5
        timer = threading.Timer(wait_time, lambda: Node.__handle_timeout(hashed_query))
        timer.start()
        with Node.query_states_lock:
            Node.query_states[hashed_query]["timeout_timer"] = timer
        documents = Node.__send_answer_to_client(hashed_query, ip_client)
        return ip_client, documents

    @classmethod
    def __handle_timeout(cls, hashed_query):
        with cls.query_states_lock:
            if hashed_query in cls.query_states:
                state = cls.query_states[hashed_query]
                if state["timeout_timer"]:
                    state["timeout_timer"].cancel()
                while not Node.responses_queue.empty():
                    state["responses_list"].append(Node.responses_queue.get())
                logger.debug("Respuestas recibidas:", state["responses_list"])

    @classmethod
    def __send_answer_to_client(cls, hashed_query, ip_client):
        with cls.query_states_lock:
            state = cls.query_states[hashed_query]
            controller = DocumentoController(f"leader/{ip_client}")
            model = Retrieval_Vectorial()
            [controller.create_document(doc) for _, doc in state["responses_list"] if _ == hashed_query]
            documents = model.retrieve(state["query"], controller, 10)
            controller.delete_all_documents()
            del cls.query_states[hashed_query]
        return documents

     # Start server method to handle incoming requests
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.debug(f"start server : {(self.ip, self.port)}")
            
            s.bind((self.ip, self.port))
            s.listen(10)

            while True:
                conn, addr = s.accept()
                logger.debug(f'new connection from {addr}')

                data = conn.recv(1024).decode().split(',')
                
                if data == ['']:
                    logger.debug(f"No hay data de {addr}")
                    continue
                    

                data_resp = None
                option = int(data[0])

                if option == FIND_SUCCESSOR:
                    id = int(data[1])
                    data_resp = self.find_succ(id)
                elif option == FIND_PREDECESSOR:
                    id = int(data[1])
                    data_resp = self.find_pred(id)
                elif option == GET_SUCCESSOR:
                    data_resp = self.succ if self.succ else self.ref
                elif option == GET_PREDECESSOR:
                    data_resp = self.pred if self.pred else self.ref
                # elif option == NOTIFY:
                #     id = int(data[1])
                #     ip = data[2]
                #     self.notify(ChordNodeReference(ip, self.port))
                elif option == NOTIFY:
                    ip = data[2]
                    self.notify(ChordNodeReference(ip, self.port))
                elif option == CHECK_PREDECESSOR:
                    pass
                elif option == CLOSEST_PRECEDING_FINGER:
                    id = int(data[1])
                    data_resp = self.closest_preceding_finger(id)
                elif option == STORE_KEY:
                    key, value = data[1], data[2]
                    self.data[key] = value
                elif option == RETRIEVE_KEY:
                    key = data[1]
                    data_resp = self.data.get(key, '')
                elif option == SEARCH:
                    query = data[1]
                    data_resp = self.search(query)
                elif option == JOIN:
                    # logger.debug(f'JOIN data msg : {data[0]} - {self.ip}')
                    chord_node_ref = ChordNodeReference(data[2])
                    if chord_node_ref:
                        logger.debug(f'join to the chord network - {self.ip}')
                        # logger.debug(f'I have the chord node ip to for join to the chord network : {self.ip}')
                        logger.debug(f'node_reference - {chord_node_ref.ip}')
                        self.join(chord_node_ref)
                elif option == JOIN and not self.succ:
                    ip = data[2]
                    self.join(ChordNodeReference(ip, self.port))
                # elif option == FIND_LEADER and self.is_leader:
                #     logger.debug("Entra al if correcto")
                #     response = f'{self.ip}'.encode()
                #     conn.sendall(response)
                    
                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()
                
    def run(self):
        if self.is_leader:
            threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
            self.listen_for_clients()
