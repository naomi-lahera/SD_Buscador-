import socket
import threading, multiprocessing
import sys
import time
import logging
import hashlib

from node.bully import BullyBroadcastElector
from data_access_layer.controller_interface import BaseController


# from node.leader import Leader

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

MCAST_PORT = '8002'
MCAST_ADRR = '224.0.0.1'

BCAST_PORT = '8002'

# Operation codes
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
REPLICATE = 21
ADD_DOC = 22
CHECK_LEADER = 23
STABILIZE_DATA_1 = 24
STABILIZE_DATA_2 = 22
NOTIFY_PRED = 30
CHECK_NODE = 31
#------------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3


# Configurar el nivel de log
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
logging.basicConfig(level=logging.DEBUG,
                     format='%(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

# # Function to hash a string using SHA-1 and return its integer representation
# def getShaRepr(data: str):
#     return int(hashlib.sha1(data.encode()).hexdigest(), 16)

def getShaRepr(data: str, max_value: int = 16):
    # Genera el hash SHA-1 y obtén su representación en hexadecimal
    data = str(data)
    hash_hex = hashlib.sha1(data.encode()).hexdigest()
    hash_int = int(hash_hex, 16)
    values = list(range(max_value + 1))
    index = hash_int % len(values)

    return values[index]

# Class to reference a Chord node
class ChordNodeReference:
    def __init__(self, ip: str, port: int = 8001):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port

    # Internal method to send data to the referenced node
    def _send_data(self, op: int, data: str = None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                logger.debug(f'_send_data: {self.ip}: {op}')
                if op == CHECK_NODE: s.settimeout(2)
                s.connect((self.ip, self.port))
                s.sendall(f'{op},{data}'.encode('utf-8'))
                logger.debug(f'_send_data end: {self.ip}')
                return s.recv(1024)
        except Exception as e:
            logger.debug(f"Error sending data: {e}")
            return b''
        
    # Internal method to send data to all nodes
    def _send_data_global(self, op: int, data: str = None) -> list:
        try:
            logger.debug(f'Broadcast: {self.ip}')
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(f'{op}, {data}'.encode(), (str(socket.INADDR_BROADCAST), self.port))
            logger.debug(f'Broadcast end: {self.ip}')
            response = s.recv(1024).decode().split(',')
            logger.debug(f'Broadcast end end: {self.ip}')
            logger.debug(f'response: {response}')
            s.close()
            return response
        except Exception as e:
            logger.debug(f"Error sending Broadcast: {e}")
            return b''
        
    # Method to find a chord network node to conect
    def join(self, ip) -> list:
        logger.debug(f'join start: {self.ip}')
        # response = self._send_data_global(JOIN, str(id)).decode().split(',')
        response = self._send_data_global(JOIN, ip)
        # # logger.debug(f'join msg : {ip} - {self.ip}')
        logger.debug(f'join end: {self.ip}')
        return response
        # return ChordNodeReference(response[1], self.port)
             
    # Method to find the successor of a given id
    def find_successor(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(FIND_SUCCESSOR, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Method to find the predecessor of a given id
    def find_predecessor(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(FIND_PREDECESSOR, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Property to get the successor of the current node
    @property
    def succ(self) -> 'ChordNodeReference':
        response = self._send_data(GET_SUCCESSOR).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Property to get the predecessor of the current node
    @property
    def pred(self) -> 'ChordNodeReference':
        response = self._send_data(GET_PREDECESSOR).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Method to notify the current node about another node
    def notify(self, node: 'ChordNodeReference'):
        self._send_data(NOTIFY, f'{node.id},{node.ip}')

    def notify_pred(self, node: 'ChordNodeReference'):
        self._send_data(NOTIFY_PRED, f'{node.id},{node.ip}')

    # Method to check if the predecessor is alive
    def check_node(self):
        return self._send_data(CHECK_NODE)

    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        response = self._send_data(CLOSEST_PRECEDING_FINGER, str(id)).decode().split(',')
        return ChordNodeReference(response[1], self.port)
    
    # Method to store a key-value pair in the current node
    def store_key(self, key: str, value: str):
        self._send_data(STORE_KEY, f'{key},{value}')

    # Method to retrieve a value for a given key from the current node
    def retrieve_key(self, key: str) -> str:
        response = self._send_data(RETRIEVE_KEY, key).decode()
        return response
    
    def replicate(self, key: str, value: str, node: int):
        self._send_data(REPLICATE, f'{key},{value},{node}')
        
    def stabilize_data_step1(self, own, replicate):
        self._send_data(STABILIZE_DATA_1, f'{own},{replicate}')
        
    def stabilize_data_step2(self, own, replicate):
        self._send_data(STABILIZE_DATA_2, f'{own},{replicate}')

    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)


class ChordNode():
    def __init__(self, controller: BaseController, ip: str, port: int = 8001, m: int = 4):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.succ = self.ref
        self.pred = None
        self.m = m  # Number of bits in the hash/key space
        self.finger = [self.ref] * self.m  # Finger table
        self.next = 0  # Finger table index to fix next
        self.data = {}  # Dictionary to store key-value pairs
        
        self.controller = controller

        # Start background threads for stabilization, fixing fingers, and checking predecessor
        #threading.Thread(target=self.stabilize, daemon=True).start()  # Start stabilize thread
        # threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        
        # threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        #threading.Thread(target=self._reciev_broadcast, daemon=True).start() ## Reciev broadcast message

        
#____________________________________________________________OK______________________________________________________________________#
        # self.m = m # Number of bits in the hash/key spac

        # self.finger = [self.ref] * self.m  # Finger table
        # # print(f'm : {self.m}')
        # self.next = 0  # Finger table index to fix next

#_____________________________________________________BULLY___________________________________________________________________________#
        self.e = BullyBroadcastElector()
        threading.Thread(target=self.e.loop, daemon=True).start()
     

    # Helper method to check if a value is in the range (start, end]
    def _inbetween(self, k: int, start: int, end: int) -> bool:
        if start < end:
            return start < k <= end
        else:  # The interval wraps around 0
            return start < k or k <= end
    
    # Method to find the successor of a given id
    def find_succ(self, id: int) -> 'ChordNodeReference':
        node = self.find_pred(id)  # Find predecessor of id
        return node.succ  # Return successor of that node

    # Method to find the predecessor of a given id
    def find_pred(self, id: int, direction=True) -> 'ChordNodeReference':
        node = self
        if direction:
            while not self._inbetween(id, node.id, node.succ.id):
                node = node.succ
        else:
            while not self._inbetween(id, node.pred.id, node.id):
                node = node.pred
        return node
    
    # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        for i in range(self.m - 1, -1, -1):
            if self.finger[i] and self._inbetween(self.finger[i].id, self.id, id):
                return self.finger[i].closest_preceding_finger(id)
        
        return self.ref

    # Method to join a Chord network using 'node' as an entry point
    def join(self, node: 'ChordNodeReference'):
        if node:
            self.pred = None
            self.succ = node.find_successor(self.id)
            self.succ.notify(self.ref)
        else:
            self.succ = self.ref
            self.pred = None

    # Internal method to send data to all nodes
    #def _send_broadcast(self, op: int, data: str = None) -> bytes:
    #        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #        # s.sendto(f'{op},{data}'.encode(), (str(socket.INADDR_BROADCAST), self.port))
    #        s.sendto(f'{op},{data}'.encode(), (str(socket.INADDR_BROADCAST), int(BCAST_PORT)))
    #        s.close()
    #        logger.debug(f'Broadcast sended')


    # # Method to find the successor of a given id
    # def find_succ(self, id: int) -> 'ChordNodeReference':
    #     node = self.find_pred(id)  # Find predecessor of id
    #     try:
    #         return node.successor
    #     except:
    #         return self.ref # Return successor of that node

    # # Method to find the predecessor of a given id
    # def find_pred(self, id: int) -> 'ChordNodeReference':
    #     # logger.debug(f'Entro a find_pred {self.id}')
    #     node = self
    #     try:
    #         while not self._inbetween(id, node.id, node.succ.id):
    #             node = node.closest_preceding_finger(id)
    #     except:
    #         logger.debug(f'isinstance: {isinstance(node, ChordNodeReference)}')
    #         return node if isinstance(node, ChordNodeReference) else self.ref

#_______________________________________________OK___________________________________________________________________#
    # Method to find the closest preceding finger of a given id
    # def closest_succeding_finger(self, id: int) -> 'ChordNodeReference':
    #     for i in range(self.m):
    #         if self.finger[i] and self._inbetween(id, self.id, self.finger[i].id):
    #             return self.finger[i]
    #     return self.ref
#___________________________________________________________________________________________________________________#


#_______________________________________PENDIENTE A PRUEBA__________________________________________________________#    
     # Method to find the closest preceding finger of a given id
    # def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
    #     for i in range(self.m - 1, -1, -1):
    #         if self.finger[i] and self._inbetween(self.finger[i].id, self.id, id):
    #             return self.finger[i]
    #     return self.ref
#____________________________________________________________________________________________________________________#

    def find_succ(self, id: int) -> 'ChordNodeReference':
        if not self.pred: # Existe unúnico nodo en el anillo
            return self.ref

        # logger.debug(f'closest_succeding_finger de {id} : {self.closest_succeding_finger(id)}')

        if self.id < id: # Mi sucesor es mejor candidato a sucesor que yo
            if self.succ.id > self.id: # # Mi sucesor es mejor candidato a sucesor que yo
                # closest_succeding_finger = self.closest_succeding_finger(id)
                return self.succ.find_successor(id)
                # return closest_succeding_finger.find_successor(id)
            else:
                return self.succ # El nodo esta entre yo y mi sucesor. El sucesor el mi sucesor
        else: # Soy candidatoa  sucesor
            if self.pred.id < self.id: # Verificacion de que soy el menor de los mayores
                if self.pred.id > id: # Mi predecesor es mejor candidato a sucesor que yo
                    # closest_preceding_finger = self.closest_preceding_finger(id)
                    return self.pred.find_successor(id)
                    # return closest_preceding_finger.find_successor(id)
                else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                    return self.ref
            else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                return self.ref

    def join(self, node: 'ChordNodeReference'):
        if node:
            self.pred = None
            self.succ = node.find_successor(self.id)
            self.succ.notify(self.ref)
        else:
            self.succ = self.ref
            self.pred = None

    # Method to join a Chord network without 'node' reference as an entry point
    def joinwr(self):
        logger.debug(f'join_CN: {self.ip}')
        # self.ref.join(self.ip)
        msg = self.ref.join(self.ref)
        logger.debug(f'join_CN msg: {msg}')
        return self.join(ChordNodeReference(msg[2], self.port))

    def stabilize(self):
        """Regular check for correct Chord structure."""
        while True:
            if self.succ.id != self.id:
                logger.debug('stabilize')
                if self.succ.check_node() != b'':
                    x = self.succ.pred
                    if x.id != self.id:
                        logger.debug(x)
                        if x and self._inbetween(x.id, self.id, self.succ.id):
                            self.succ = x
                        self.succ.notify(self.ref)

            logger.debug(f"successor : {self.succ} predecessor {self.pred}")
            time.sleep(10)

    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        if not self.pred or self._inbetween(node.id, self.pred.id, self.id):
            self.stabilize_data(node)
            self.pred = node

#_____________________________________________________________OK________________________________________________________________________#
    # Fix fingers method to periodically update the finger table
    # def fix_fingers(self):
    #     while True:
    #         try:
    #             for node_index in range(len(self.finger)):
    #                 self.finger[node_index] = self.find_succ((self.id + 2**node_index) % 2**self.m)
    #         except Exception as e:
    #             print(f"Error in fix_fingers: {e}")

    #         for index, node in enumerate(self.finger):
    #             logger.debug(f'node: {index} succesor: {node}')

    #         time.sleep(10)
#________________________________________________________________________________________________________________________________________#

    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        logger.debug(f'in notify, my id: {self.id} my pred: {node.id}')
        if node.id == self.id:
            pass
        elif not self.pred:
            self.pred = node
            if self.id == self.succ.id:
                self.succ = node
                
                self.stabilize_data(node) # Replicacion
                
                self.succ.notify(self.ref)
                
        elif self._inbetween(node.id, self.pred.id, self.id):
            self.pred.notify_pred(node)
            self.pred = node

    def notify_pred(self, node: 'ChordNodeReference'):
        logger.debug(f'in notify_pred, my id: {self.id} my succ: {node.id}')
        self.succ = node

    # Reciev boradcast message
    def _reciev_broadcast(self):
        logger.debug("recive broadcast de chord")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.bind(('', int(self.port)))
        s.bind(('', int(self.port)))

        # logger.debug(f'running _reciev_broadcast running')

        while True:
            logger.debug(f"recive broadcast de chord in while por el puerto {self.port}!!!")
            
            msg, addr = s.recvfrom(1024)

            # logger.debug(f'Received broadcast: {self.ip}')

            msg = msg.decode().split(',')
            # logger.debug(f'received broadcast msg: {msg}')
            logger.debug(f"recive broadcast de chord in while before try!!!")
            try:
                
                option = int(msg[0])
                logger.debug(f"recive broadcast de chord option {option}")
                if option == REQUEST_BROADCAST_QUERY:
                    hashed_query, query = msg[1].split(',', 1)  # Asume que el mensaje recibido tiene la forma: hash,query
            
                    # Verifica si el mensaje es una respuesta a nuestra consulta actual
                    if hasattr(self, None) and self.hash_query == hashed_query:
                        # Pone la respuesta en la cola de respuestas del Leader
                        self.responses_queue.put(query)
                
                if option == JOIN:
                    # msg[2] es el ip del nodo
                    if msg[2] == self.ip:
                        logger.debug(f'My own broadcast msg: {self.id}')
                    else:
                        # self.ref._send_data(JOIN, {self.ref})
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                logger.debug(f'_send_data: {self.ip}')
                                s.connect((msg[2], self.port))
                                s.sendall(f'{JOIN},{self.ref}'.encode('utf-8'))
                                logger.debug(f'_send_data end: {self.ip}')
                        except Exception as e:
                            logger.debug(f"Error sending data: {e}")
                    #TODO Enviar respuesta
                
                if option == FIND_LEADER:
                    print("Entra al if correcto en chord")
                    # Asegúrate de que msg[1] contiene la dirección IP del cliente que hizo el broadcast
                    ip_client = msg[1].strip()  # Elimina espacios en blanco
                    response = f'{self.ip},{self.port}'.encode()  # Prepara la respuesta con IP y puerto del líder
                    print("-----------------------------------------")
                    print(f"enviando respuesta {response} a {(ip_client,8003)}")
                    print("-----------------------------------------")

                    s.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente
                    
                    
            except Exception as e:
                print(f"Error in _receiver_boradcast: {e}")

    def check_predecessor(self):
        while True:
            if self.pred and self.pred.check_node() == b'':
                logger.debug('\n\n\n ALARMA!!! PREDECESOR PERDIDO!!! \n\n\n')
                self.e.Leader = self.ip
                self.e.InElection = True
                self.e.ImTheLeader = True
                self.e.election_call()
                self.pred = self.find_pred(self.pred.id)
                self.pred.notify_pred(self.ref)
            time.sleep(10)

    # Store key method to store a key-value pair and replicate to the successor
    def store_key(self, key: str, value: str):
        key_hash = getShaRepr(key)
        node = self.find_succ(key_hash)
        node.store_key(key, value)
        # self.data[key] = value  # Store in the current node
        # self.succ.store_key(key, value)  # Replicate to the successor
        
        # Retrieve key method to get a value for a given key
    def retrieve_key(self, key: str) -> str:
        key_hash = getShaRepr(key)
        node = self.find_succ(key_hash)
        return node.retrieve_key(key)
             
    def reasign(self,new: ChordNodeReference, node: int):
        min = self.pred.id if node == 1 else self.id
        max = self.id if node == 1 else self.succ.id 
        
        store = self.controller.get_docs_between([-1, node], min, new.id) # llaves que tiene que guardar el actual predecesor own_pred_keys[old_predeccesro_id : new_predeccesor_id - 1]
        own_keys = self.controller.get_docs_between([-1, node], new.id, max)  # own_pred_keys[new_predeccesor_id : self.id - 1]
        
        return own_keys, store if node == 1 else store, own_keys
             
    # node dice si se va a tomar la tabla del predecesor o la del sucesor
    def stabilize_data(self, new: ChordNodeReference):
        keep, keep_new = self.reasign(new, 0)
        
        self.controller.create_doc_list(keep, -1)
        self.controller.create_doc_list(keep_new, 0)
        
        new.stabilize_data_step1(keep_new, keep)
        
    def stabilize_data_step1(self, own, replicate):
        keep, keep_new = self.reasign(self.succ, 1)
    
        self.controller.create_doc_list(keep + own, -1)
        self.controller.create_doc_list(keep_new + replicate, 1)
        
        self.succ.stabilize_data_step2(keep_new, keep)
        
    def stabilize_data_step2(self, own, replicate):
        self.controller.create_doc_list(own, -1)
        self.controller.create_doc_list(replicate, 1)
        
        
        
        
        