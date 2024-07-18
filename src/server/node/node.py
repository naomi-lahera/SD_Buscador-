import time
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
QUEUE = 25
SEARCH_CLIENT = 26
GET_DOCS = 27
GET_DOCS_LEADER = 28
DELETE_LEADER = 29
DELETE = 30
UPDATE_LEADER = 31
UPDATE = 32

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
        if table == 'documentos':            
            if self.pred:
                #logger.debug("I have predeccesor")
                self.pred._send_data(INSERT, f'replica_succ,{document}')
            if self.succ.id != self.id:
                #logger.debug("I have succesor")
                self.succ._send_data(INSERT, f'replica_pred,{document}')
            
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
            
            received = msg.decode('utf-8').split(',') 
            
            option = received[0]
            ip_client = received[1]
            
            try:
                text = ','.join(received[2:])
                logger.debug(f'TEXTO: \n {text}')
            except:
                text = ''
            
            option = int(option)
            
            if option == QUERY_FROM_CLIENT and self.e.ImTheLeader:
                print("////////////////")
                print("RECIBIDO QUERY")
                print("////////////////")
                # print(f"RECIBIDO QUERY sended to {(client_to_send,8004)}")
                #response = f'Hola SERVER'.encode()  # Prepara la respuesta con IP y puerto del líder
                #broadcast_socket.sendto(response, (ip_client,8004))  # Envía la respuesta al cliente
                #return
                #TODO: Hay q hacer esto.....

                client_to_send ,documents = self.receive_query_from_client(text,ip_client)
                
                response = f'{SEARCH},{documents}'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (client_to_send,8004))  # Envía la respuesta al cliente
                print(f"{documents} sended to {(client_to_send,8004)}")
                
            elif option == FIND_LEADER and self.e.ImTheLeader:
                #logger.debug("finding leader")
                if self.e.ImTheLeader:
                    #logger.debug("///////////////////////////////////////////////////////")
                    
                    response = f'{self.e.Leader},{self.leader_port}'.encode()  # Prepara la respuesta con IP y puerto del líder
                    #logger.debug(f'==========={self.e.Leader},{self.leader_port}===========')
                    #logger.debug(f'==========={ip_client}===========')
                    broadcast_socket.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente
                    
            elif option == INSERT and self.e.ImTheLeader:
                #logger.debug('*******************************************************************')
                #logger.debug('                         INSERT                                    ')
                #logger.debug('*******************************************************************')
                #logger.debug(f'\n\nTHE TEXT:\n\n{text}\n\n')
                
                id = getShaRepr(text)
                #logger.debug(f'----------------------ID: {id}-------------------------------------')
                
                node: ChordNodeReference = self.find_succ(id)
                #logger.debug(f'______________________SUCCESOR: {node}______________________________')
                
                logger.debug('*******************************************************************')
                logger.debug('                        INSERT LEADER                              ')
                logger.debug(f'                        ID:  {id}                                 ')
                logger.debug(f'                     FROM:  {self.id}                             ')
                logger.debug(f'                     TO:  {node.id}                               ')
                logger.debug('*******************************************************************')
                
                if node.id != self.id:
                    node._send_data(INSERT,f'documentos,{text}')
                else:
                    self.add_doc(id, text, 'documentos')
                    
                response = f'Loaded DOCUMENT'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (ip_client,8004))  # Envía la respuesta al cliente
                
            elif option == GET_DOCS_LEADER and self.e.ImTheLeader:
                client_to_send, docs = self.get_all_nodes_docs(ip_client)
                
                response = f'{GET_DOCS_LEADER},{docs}'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (client_to_send,8004))  # Envía la respuesta al cliente
                print(f"{docs} sended to {(client_to_send, 8004)}")
                
            elif option == DELETE_LEADER and self.e.ImTheLeader:           
                id = int(received[1])
                node: ChordNodeReference = self.find_succ(id)
                
                logger.debug('*******************************************************************')
                logger.debug('                        DELETE LEADER                              ')
                logger.debug(f'                        ID:  {id}                                 ')
                logger.debug(f'                       NODE:  {node.id}                           ')
                logger.debug('*******************************************************************')
                
                if node.id != self.id:
                    node._send_data(DELETE,f'{id},documentos')
                else:
                    self.del_doc(id, 'documentos')
                    
                    if self.pred:
                        self.pred._send_data(DELETE, f'{id},replica_succ')
                    if self.succ.id != self.id:
                        self.succ._send_data(DELETE, f'{id},replica_pred')
                    
                response = f'Deleted DOCUMENT'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (ip_client,8004))  # Envía la respuesta al cliente
                
            elif option == UPDATE_LEADER and self.e.ImTheLeader:
                id = int(received[1])
                node: ChordNodeReference = self.find_succ(id)
                
                logger.debug('*******************************************************************')
                logger.debug('                        UPDATE LEADER                              ')
                logger.debug(f'                        ID:  {id}                                 ')
                logger.debug(f'                       NODE:  {node.id}                           ')
                logger.debug('*******************************************************************')
                
                if node.id != self.id:
                    node._send_data(UPDATE,f'{id},{text},documentos')
                else:
                    self.upd_doc(id, text, 'documentos')
                    if self.pred:
                        self.pred._send_data(UPDATE, f'{id},replica_succ')
                    if self.succ.id != self.id:
                        self.succ._send_data(UPDATE, f'{id},replica_pred')
                    
                response = f'Deleted DOCUMENT'.encode()  # Prepara la respuesta con IP y puerto del líder
                broadcast_socket.sendto(response, (ip_client,8004))  # Envía la respuesta al cliente
                
    def get_all_nodes_docs(self, ip_client: str):
        self.send_broadcast(8001, f'{GET_DOCS}')
        
        documents = dict()
        
        t = threading.Thread(target=self.start_server_to_receive_responses, args=(8002, documents))
        t.start()
        
        
        t.join()
        
        logger.debug(f'\n\n\nNode documents : \n {documents}\n\n\n')
        
        return ip_client, documents
                    
    def receive_query_from_client(self, query: str, ip_client: str):
        
        data_to_send = f'{SEARCH_CLIENT},{query}'
        self.send_broadcast(8001, data_to_send)
    
        # Cola para almacenar las respuestas recibidas de manera segura entre hilos
        responses = Queue()
        
        # Iniciar un servidor en el puerto 8002 para recibir respuestas
        print("PA LA QUEUE=======")
        server_thread = threading.Thread(target=self.start_server_to_receive_responses, args=(8002, responses))
        server_thread.start()
    
        # Espera un tiempo determinado antes de detener el servidor y recoger respuestas
        # wait_time = 2  # Tiempo de espera en segundos
        # time.sleep(wait_time)  # Espera antes de detener el servidor

        # Detiene el servidor y recoge las respuestas
        server_thread.join()

        # Convertir las respuestas de la cola a una lista
        documents = []
        print(f"QUEUE :{responses}")
        
        while not responses.empty():
            documents.append(responses.get())

        print(f"DOCUMENTS {documents}")
        return ip_client, documents
            
    def start_server_to_receive_responses(self, port, response_queue):
        """
        Inicia un servidor temporal en el puerto especificado para recibir respuestas.
        Las respuestas recibidas se agregan a la cola dada.
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(2)
            server_socket.bind(('', port))
            print("/////////////////")
            print("///////BEFORE MESSAGE//////////")
            print("/////////////////")
            
            now = time.time()
            while time.time() - now <= 5000:
                try:
                    print(time.time() - now)
                    message, addr = server_socket.recvfrom(1024)
                    message = message.decode()
                    message = message.split(",")
                    option = int(message[0])
                    
                    if option == SEARCH:
                        text = (",").join(message[1:])
                        text = message[1]

                        print(f"//////DEL NODO PA LA COLA {option}////////")
                        print(f"//////{text}///////")
                        print("/////////////////")
                        # if option == SEARCH:
                        response_queue.put(text)
                        
                    if option == GET_DOCS:
                        logger.debug(f'\n\n\nMessage:\n {message[1:]}\n\n\n')
                        response_queue[message[1]] = message[2]
                except:
                    break
                
                
        except Exception:
            print("Exploto esta talla")
        finally:
            server_socket.close()
            
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
                self.succ._send_data(REMOVE, f'replica_pred,{doc[0]}')
            
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
                # if self.pred:
                #     self.pred._send_data(INSERT, f'replica_succ,{doc[1]}')
                # if self.succ.id != self.id:
                #     self.succ._send_data(INSERT, f'replica_pred,{doc[1]}')

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

    # Reciev boradcast message
    def _reciev_broadcast(self):
        # #logger.debug("recive broadcast de chord")
        

        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # s.bind(('', int(self.port)))
            s.bind(('', int(self.port)))
            # #logger.debug(f"recive broadcast de chord in while por el puerto {self.port}!!!")
            
            msg, addr = s.recvfrom(1024)

            # #logger.debug(f'Received broadcast: {self.ip}')

            msg = msg.decode().split(',')
            # #logger.debug(f'received broadcast msg: {msg}')
            # #logger.debug(f"recive broadcast de chord in while before try!!!")
            # try:
                
            option = int(msg[0])
            # #logger.debug(f"recive broadcast de chord option {option}")
            # if option == REQUEST_BROADCAST_QUERY:
            #     hashed_query, query = msg[1].split(',', 1)  # Asume que el mensaje recibido tiene la forma: hash,query
        
            #     # Verifica si el mensaje es una respuesta a nuestra consulta actual
            #     if hasattr(self, None) and self.hash_query == hashed_query:
            #         # Pone la respuesta en la cola de respuestas del Leader
            #         self.responses_queue.put(query)
            
            if option == JOIN:
                # msg[2] es el ip del nodo
                if msg[2] == self.ip:
                    #logger.debug(f'My own broadcast msg: {self.id}')
                    continue
                else:
                    # self.ref._send_data(JOIN, {self.ref})
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            # #logger.debug(f'_send_data: {self.ip}')
                            s.connect((msg[2], self.port))
                            s.sendall(f'{JOIN},{self.ref}'.encode('utf-8'))
                            # #logger.debug(f'_send_data end: {self.ip}')
                            continue
                    except Exception as e:
                        #logger.debug(f"Error sending data: {e}")
                        continue
                #TODO Enviar respuesta
            
            # if option == FIND_LEADER:
            #     # print("Entra al if correcto en chord")
            #     # Asegúrate de que msg[1] contiene la dirección IP del cliente que hizo el broadcast
            #     ip_client = msg[1].strip()  # Elimina espacios en blanco
            #     response = f'{self.ip},{self.port}'.encode()  # Prepara la respuesta con IP y puerto del líder
            #     # print("-----------------------------------------")
            #     # print(f"enviando respuesta {response} a {(ip_client,8003)}")
            #     # print("-----------------------------------------")
            #     s.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente
            if option == SEARCH_CLIENT:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        print("////////")
                        print(f'\n\n"option search"\n\n')
                        print("////////")
                        query = ','.join(msg[1:])
                        response = f"{SEARCH},{self.search(query)}".encode()
                        print("////RESPONSE////")
                        print(f'\n\n{response}\n\n')
                        print("////////")
                        # self.send_broadcast(8002,response)
        
                        # #logger.debug(f'_send_data: {self.ip}')
                        # s.connect(('<broadcast>', 8002))
                        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                        
                        s.sendto(response, (str(socket.INADDR_BROADCAST), 8002))
                        
                        # s.sendall()
                        # #logger.debug(f'_send_data end: {self.ip}')
                        continue
                except Exception as e:
                    #logger.debug(f"Error sending data: {e}")
                    continue
                
            elif option == GET_DOCS:
                data_resp = self.get_docs('documentos')
                logger.debug(f'NODE: {self.id} DOCUMMENTS: \n {data_resp}')
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    response = f'{GET_DOCS},{data_resp}'.encode()
                    
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.sendto(response, (str(socket.INADDR_BROADCAST), 8002))
                
            
            # except Exception as e:
            #     print(f"Error in _receiver_boradcast: {e}")


    def data_receive(self, conn: socket, addr, data: list):
        data_resp = None 
        option = int(data[0])
        #logger.debug(f'ip {self.ip} recv {option}')

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
            #logger.debug('*******************************************************************')
            #logger.debug('                         INSERT                                    ')
            #logger.debug('*******************************************************************')
            table = data[1]
            text = ','.join(data[2:])
            
            logger.debug(f'\n\nTHE TEXT:\n\n{text}\n\n')
            # id = getShaRepr(','.join(data[2:min(len(data),6)]))
            id = getShaRepr(text)
            
            
            logger.debug(f"COMO SE VA  A GUARDAR")
            logger.debug(f"{id}, {text}, {table}")
            logger.debug(f"====================")
            
            self.add_doc(id, text, table)
            
            # if table == 'documentos':
            #     self.pred._send_data(INSERT, f'replica_succ,{text}')
            #     self.succ._send_data(INSERT, f'replica_pred,{text}')

        elif option == GET:
            id = data[1]
            data_resp = self.get_doc_by_id(id)[0]

        elif option == REMOVE:
            table = data[1]
            id = data[2]
            data_resp = self.del_doc(id, table)
            
            if table == 'documentos':
                if self.pred: self.pred._send_data(REMOVE, f'replica_succ,{id}')
                if self.succ.id != self.id: self.succ._send_data(REMOVE, f'replica_pred,{id}')

        elif option == EDIT:
            table = data[1]
            id = data[2]
            text = ','.join(data[3:])
            self.upd_doc(id, text, table)
                    
            if table == 'documentos':
                if self.pred: self.pred._send_data(EDIT, f'replica_succ,{id},{text}')
                if self.succ.id != self.id: self.succ._send_data(EDIT, f'replica_pred,{id},{text}')

        elif option == SEARCH:
            query = ','.join(data[1:])
            #logger.debug(f'\n\n{query}\n\n')
            response = self.search(query)
            id = response[0][1]
            text = response[0][0][0]
            text = text.split()
            text = text[:min(20, len(text))]
            text = ' '.join(text)
            data_resp = (id, text)
            #logger.debug(data_resp)

        elif option == CHECK_DOCKS:
            self.check_docs_pred()
            
        elif option == DELETE:
            id = int(data[1])
            table = data[2]
            
            logger.debug('*******************************************************************')
            logger.debug('                        DELETE LEADER                              ')
            logger.debug(f'                        ID:  {id}                                 ')
            logger.debug(f'                       NODE:  {self.id}                           ')
            logger.debug('*******************************************************************')
            
            self.del_doc(id, table)
                        
            if table == 'documentos':
                if self.pred:
                    self.pred._send_data(DELETE, f'{id},replica_succ')
                if self.succ.id != self.id:
                    self.succ._send_data(DELETE, f'{id},replica_pred')
                    
        elif option == UPDATE:
            id = int(data[1])
            table = data[2]
            text = ''.join(data[:3])
            
            logger.debug('*******************************************************************')
            logger.debug('                        UPDATE LEADER                              ')
            logger.debug(f'                        ID:  {id}                                 ')
            logger.debug(f'                       NODE:  {self.id}                           ')
            logger.debug('*******************************************************************')
            
            self.del_doc(id, table)
            
            if table == 'documentos':
                if self.pred:
                    self.pred._send_data(UPDATE, f'{id},replica_succ')
                if self.succ.id != self.id:
                    self.succ._send_data(UPDATE, f'{id},replica_pred')
                
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
                
                #logger.debug(f'new connection from {addr}')

                data = conn.recv(1024).decode().split(',') # Divide el string del mensaje por las ","

                threading.Thread(target=self.data_receive, args=(conn, addr, data)).start()
            
        
