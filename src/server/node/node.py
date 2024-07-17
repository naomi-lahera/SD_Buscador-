from node.chord.chord import ChordNode, ChordNodeReference, getShaRepr
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
CHECK_NODE = 6
CLOSEST_PRECEDING_FINGER = 7
STORE_KEY = 8
RETRIEVE_KEY = 9
SEARCH = 10
JOIN = 11
NOTIFY_PRED = 12
GET = 13
INSERT = 14
REMOVE = 15
EDIT = 16
CHECK_DOCKS = 17
FIND_LEADER = 18
REQUEST_BROADCAST_QUERY = 19
QUERY_FROM_CLIENT = 20
REPLICATE = 21
ADD_DOC = 22
STABILIZE_DATA_2 = 23
STABILIZE_DATA_1 = 24


def read_or_create_db(controller):
    connect = controller.connect()
    
    cursor = connect.cursor()
    cursor.execute('''
        DROP TABLE IF EXISTS documentos;
        ''')
    cursor.execute('''
        CREATE TABLE documentos (
        	id INTEGER PRIMARY KEY,
        	text TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        
    cursor.execute('''
        DROP TABLE IF EXISTS replica_succ;
        ''')
    cursor.execute('''
        CREATE TABLE replica_succ (
        	id INTEGER PRIMARY KEY,
        	text TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        
    cursor.execute('''
        DROP TABLE IF EXISTS replica_pred;
        ''')
    cursor.execute('''
        CREATE TABLE replica_pred (
        	id INTEGER PRIMARY KEY,
        	text TEXT NOT NULL,
        	tf TEXT
        );
        ''')
    connect.commit()
    connect.close()    
class Node(ChordNode):
    responses_queue = Queue()
    query_states = {}
    query_states_lock = threading.Lock()

    def __init__(self, ip: str, port: int = 8001, m: int = 4,leader_ip = '172.17.0.2',leader_port = 8002):
        super().__init__(ip, port, m)
        self.controller = DocumentoController(self.ip)
        read_or_create_db(self.controller)
        self.logger = logging.getLogger(__name__)
        self.is_leader = False
        self.data = {}
        self.model = Retrieval_Vectorial()
        self.leader_ip = leader_ip
        self.leader_port = leader_port
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        threading.Thread(target=self.stabilize, daemon=True).start()  # Start stabilize thread
        # threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        threading.Thread(target=self.check_predecessor, daemon=True).start()  # Start check predecessor thread
        threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
        threading.Thread(target=self._reciev_broadcast, daemon=True).start() ## Reciev broadcast message

       
    
    def add_doc(self, id, document, table):
        return self.controller.create_document(id, document, table)
    
    def upd_doc(self, id, text, table):
        return self.controller.update_document(id, table, text)
    
    def del_doc(self, id, table):
        return self.controller.delete_document(id, table)
    
    def get_docs(self, table):
        return self.controller.get_documents(table)
    
    def get_doc_by_id(self, id):
        return self.controller.get_document_by_id(id)
    
    def search(self, query):
        return self.model.retrieve(query, self.controller)
    
    def notify(self, node: 'ChordNodeReference'):
        super().notify(node)
        self.check_docs()
        self.pred._send_data(CHECK_DOCKS)
    
    def get_docs_between(self, tables, min, max):
        return self.controller.get_docs_between(tables, min, max)

    def listen_for_broadcast(self):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        broadcast_socket.bind(('', self.port+1))
        while True:
            # print(f"PUERTO: {self.port+1}")
            msg, client_address = broadcast_socket.recvfrom(1024)
            logger.debug(f"Broadcast recibido de {client_address}: {msg.decode('utf-8')}")
            logger.debug("\n****************************************")
            logger.debug(f"\nMensaje del cliente: {msg.decode('utf-8').split(',')}")
            logger.debug("\n****************************************")
            option, ip_client,text = msg.decode('utf-8').split(',')
            option = int(option)
            
            if option == QUERY_FROM_CLIENT:
                print("RECIBIDO QUERY")
                # print(f"RECIBIDO QUERY sended to {(client_to_send,8004)}")
                response = f'Hola SERVER'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (ip_client,8004))  # Envía la respuesta al cliente
                return
                #TODO: Hay q hacer esto.....
                client_to_send ,documents = self.receive_query_from_client(self,text,ip_client)
                
                response = f'{documents}'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (client_to_send,8004))  # Envía la respuesta al cliente
                print(f"{documents} sended to {(client_to_send,8004)}")
                
            elif option == FIND_LEADER:
                logger.debug("finding leader")
                if self.e.ImTheLeader:
                    logger.debug("///////////////////////////////////////////////////////")
                    
                    response = f'{self.e.Leader},{self.leader_port}'.encode()  # Prepara la respuesta con IP y puerto del líder
                    logger.debug(f'==========={self.e.Leader},{self.leader_port}===========')
                    logger.debug(f'==========={ip_client}===========')
                    broadcast_socket.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente

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
                # logger.debug("Respuestas recibidas:", state["responses_list"])

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
    
    # def replicate(self, key: str, value: str):
    #     #TODO Definir cuando estoy poniendo en mi bd y cuando es en la bd de mi sucesor o predecesor
    #     self.add_doc(value)
    
    def check_docs(self):
        # toma sus documentos y las replicas de su predecesor
        my_docs = self.get_docs('documentos')
        pred_docs = self.get_docs('replica_pred')

        for doc in my_docs:
            # si el id NO esta entre su nuevo predecesor y el, o sea le pertenece a su predecesor
            if not self._inbetween(doc[0], self.pred.id, self.id):
                
                # le dice que lo inserte en sus documentos
                self.pred._send_data(INSERT, f'documentos,{doc[1]}')
                
                # lo elimina de sus documentos
                self.del_doc(doc[0], 'documentos')
            
            else:
                # esta entre los 2, asi que le pertenece al sucesor y le notifica que lo replique
                self.pred._send_data(INSERT, f'replica_succ,{doc[1]}')

        
        for doc in pred_docs:
            # si el id NO esta entre su nuevo predecesor y el, o sea le pertenece al antiguo predecesor
            if not self._inbetween(doc[0], self.pred.id, self.id):
                
                # le dice que lo replique como documento del que ahora es el predecesor del nuevo predecesor
                self.pred._send_data(INSERT, f'replica_pred,{doc[1]}')

                # lo elimina porque cambio su predecesor
                self.del_doc(doc[0], 'replica_pred')

            else:
                # si el id esta entre su nuevo predecesor y el, o sea le pertenece a el
                self.add_doc(doc[0], doc[1], 'documentos')

                # luego lo elimina de sus replicados
                self.del_doc(doc[0], 'replica_pred')

                # despues lo mandan a replicar
                self.pred._send_data(INSERT, f'replica_succ,{doc[1]}')
                self.succ._send_data(INSERT, f'replica_pred,{doc[1]}')

    # luego aqui entra el predecesor
    def check_docs_pred(self):
        
        # toma sus documentos y las replicas de su sucesor
        my_docs = self.get_docs('documentos')
        succ_docs = self.get_docs('replica_succ')

        for doc in my_docs:
           
            # los documentos que me pertenecen los replico a mi nuevo sucesor
            self.succ._send_data(INSERT, f'replica_pred,{doc[1]}')


        for doc in succ_docs:
            # si el id NO esta entre su nuevo sucesor y el, o sea le pertenece al antiguo sucesor
            if not self._inbetween(doc[0], self.id, self.succ.id):

                # le dice que lo replique como documento del que ahora es el sucesor del nuevo sucesor
                self.succ._send_data(INSERT, f'replica_succ,{doc[1]}')
                
                # lo elimina porque cambio su sucesor
                self.del_doc(doc[0], 'replica_succ')
            
            else:
                # si el id esta entre su nuevo sucesor y el, o sea le pertenece al nuevo sucesor
                self.succ._send_data(INSERT, f'documentos,{doc[1]}')

    def data_receive(self, conn: socket, addr, data: list):
        data_resp = None 
        option = int(data[0])
        logger.debug(f'ip {self.ip} recv {option}')

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

        elif option == NOTIFY:
            ip = data[2]
            self.notify(ChordNodeReference(ip, self.port))

        elif option == NOTIFY_PRED:
            ip = data[2]
            self.notify_pred(ChordNodeReference(ip, self.port))

        elif option == CHECK_NODE: data_resp = self.ref

        elif option == CLOSEST_PRECEDING_FINGER:
            id = int(data[1])
            data_resp = self.closest_preceding_finger(id)

        elif option == STORE_KEY:
            key, value = data[1], data[2]
            self.data[key] = value

        elif option == RETRIEVE_KEY:
            key = data[1]
            data_resp = self.data.get(key, '')

        elif option == JOIN and self.id == self.succ.id:
            ip = data[2]
            self.join(ChordNodeReference(ip, self.port))

        elif option == INSERT:
            table = data[1]
            text = ','.join(data[2:])
            logger.debug(f'\n\nTHE TEXT:\n\n{text}\n\n')
            id = getShaRepr(','.join(data[2:min(len(data),6)]))
            self.add_doc(id, text, table)
            
            if table == 'documentos':
                self.pred._send_data(INSERT, f'replica_succ,{text}')
                self.succ._send_data(INSERT, f'replica_pred,{text}')

        elif option == GET:
            id = data[1]
            data_resp = self.get_doc_by_id(id)[0]

        elif option == REMOVE:
            table = data[1]
            id = data[2]
            data_resp = self.del_doc(id, table)
            
            if table == 'documentos':
                self.pred._send_data(REMOVE, f'replica_succ,{id}')
                self.succ._send_data(REMOVE, f'replica_pred,{id}')

        elif option == EDIT:
            table = data[1]
            for i in range(2, len(data)):
                if data[i] == '---':
                    id = ','.join(data[1:i])
                    text = ','.join(data[i+1:])
                    self.upd_doc(id, text, table)
                    
                    if table == 'documentos':
                        self.pred._send_data(EDIT, f'replica_succ,{id},{text}')
                        self.succ._send_data(EDIT, f'replica_pred,{id},{text}')
                    break

        elif option == SEARCH:
            query = ','.join(data[1:])
            logger.debug(f'\n\n{query}\n\n')
            response = self.search(query)
            id = response[0][1]
            text = response[0][0][0]
            text = text.split()
            text = text[:min(20, len(text))]
            text = ' '.join(text)
            data_resp = (id, text)
            logger.debug(data_resp)

        elif option == CHECK_DOCKS:
            self.check_docs_pred()




        if data_resp and option == GET:
            response = data_resp.encode()
            conn.sendall(response)

        elif data_resp and option == SEARCH:
            response = f'{data_resp[0]},{data_resp[1]}'.encode()
            conn.sendall(response)

        elif data_resp:
            response = f'{data_resp.id},{data_resp.ip}'.encode()
            conn.sendall(response)
        conn.close()


    def start_server(self):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: #Crea el socket "s" con dirección IPv4 (AF_INET) y de tipo TCP (SOCK_STREAM) 
            
            #*Más configuración del socket "s"  
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # SO_REUSEADDR permite reutilizar la dirección local antes que se cierre el socket
            #? La configuración anterior nos conviene?
             
            s.bind((self.ip, self.port)) #Hace la vinculación de la dirección local de "s"
            
            s.listen(10) # Hay un máximo de 10 conexiones  pendientes

            while True:
                
                conn, addr = s.accept() #conexión y dirección del cliente respectivamente
                
                logger.debug(f'new connection from {addr}')

                data = conn.recv(1024).decode().split(',') # Divide el string del mensaje por las ","

                threading.Thread(target=self.data_receive, args=(conn, addr, data)).start()
            
        
