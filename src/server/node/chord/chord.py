import socket
import threading, multiprocessing
import sys
import time
import logging
import hashlib

from node.bully import BullyBroadcastElector
from data_access_layer.controller_bd import DocumentoController


# from node.leader import Leader

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

MCAST_PORT = '8002'
MCAST_ADRR = '224.0.0.1'

BCAST_PORT = '8002'
PORT = 8001
# Operation codes

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

#------------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3


# Function to hash a string using SHA-1 and return its integer representation
def getShaRepr(data: str, max_value: int = 16):
    print(data)
    # Genera el hash SHA-1 y obtén su representación en hexadecimal
    hash_hex = hashlib.sha1(data.encode()).hexdigest()
    
    # Convierte el hash hexadecimal a un entero
    hash_int = int(hash_hex, 16)
    
    # Define un arreglo o lista con los valores del 0 al 16
    values = list(range(max_value + 1))
    
    # Usa el hash como índice para seleccionar un valor del arreglo
    # Asegúrate de que el índice esté dentro del rango válido
    index = hash_int % len(values)
    
    # Devuelve el valor seleccionado
    return values[index]

# Class to reference a Chord node
class ChordNodeReference:
    def __init__(self, ip: str, port: int = 8001):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = PORT

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
            s.sendto(f'{op}, {data}'.encode(), (str(socket.INADDR_BROADCAST), PORT))
            logger.debug(f'Broadcast end: {self.ip}')
            response = s.recv(1024).decode().split(',')
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

    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)


# Class representing a Chord node
class ChordNode:    
    def __init__(self, ip: str, port: int = 8001, m: int = 4):
        print(f"CHORD_NODE :{ip}")
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = PORT
        self.ref = ChordNodeReference(self.ip, self.port)
        self.succ = self.ref  # Initial successor is itself
        self.pred = None  # Initially no predecessor
        self.m = m  # Number of bits in the hash/key space
        self.finger = [self.ref] * self.m  # Finger table
        self.next = 0  # Finger table index to fix next
        self.data = {}  # Dictionary to store key-value pairs
        self.controller = DocumentoController
        
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
    def join(self, node: 'ChordNodeReference' = None):
        
        if node:
            self.pred = None
            self.succ = node.find_successor(self.id)
            self.succ.notify(self.ref)
        else:
            self.succ = self.ref
            self.pred = None
      
    # Method to join a Chord network without 'node' reference as an entry point      
    def join_CN(self):
        logger.debug(f'join_CN: {self.ip}')
        # self.ref.join(self.ip)
        msg = self.ref.join(self.ref)
        logger.debug(f'join_CN msg: {msg}')
        return self.join(ChordNodeReference(msg[2], PORT))

    # Stabilize method to periodically verify and update the successor and predecessor
    def stabilize(self):
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
        logger.debug(f'in notify, my id: {self.id} my pred: {node.id}')
        if node.id == self.id:
            pass
        elif not self.pred:
            self.pred = node
            if self.id == self.succ.id:
                self.succ = node
                self.succ.notify(self.ref)
        elif self._inbetween(node.id, self.pred.id, self.id):
            self.pred.notify_pred(node)
            self.pred = node

    def notify_pred(self, node: 'ChordNodeReference'):
        logger.debug(f'in notify_pred, my id: {self.id} my succ: {node.id}')
        self.succ = node
        self.succ.notify(self.ref)

    # Fix fingers method to periodically update the finger table
    def fix_fingers(self):
        while True:
            to_write = ''
            for i in range(self.m):
                # Calcular el próximo índice de dedo
                next_index = (self.id + 2**i) % 2**self.m
                if self.succ.id == self.id:
                    self.finger[i] = self.ref
                else:
                    if self._inbetween(next_index, self.id, self.succ.id):
                        self.finger[i] = self.succ
                    else:
                        node = self.succ.closest_preceding_finger(next_index)
                        if node.id != next_index:
                            node = node.succ
                        self.finger[i] = node
                
                if i == 0 or self.finger[i-1].id != self.finger[i].id or i > 154:
                    to_write += f'>> ({i}, {next_index}): {self.finger[i].id}\n'
            logger.debug(f'fix_fingers {self.id}: {self.succ} and {self.pred}')
            logger.debug(f'{self.id}:\n{to_write}')
            time.sleep(10)

    # Check predecessor method to periodically verify if the predecessor is alive
    def check_predecessor(self):
        while True:
            if self.pred and self.pred.check_node() == b'':
                logger.debug('\n\n\n ALARMA!!! PREDECESOR PERDIDO!!! \n\n\n')
                pred = self.find_pred(self.pred.id)
                self.pred = None
                pred.notify_pred(self.ref)
            time.sleep(10)

    # Store key method to store a key-value pair and replicate to the successor
    def store_key(self, key: str, value: str):
        key_hash = getShaRepr(key)
        node = self.find_succ(key_hash)
        node.store_key(key, value)
        self.data[key] = value  # Store in the current node
        self.succ.store_key(key, value)  # Replicate to the successor

    # Retrieve key method to get a value for a given key
    def retrieve_key(self, key: str) -> str:
        key_hash = getShaRepr(key)
        node = self.find_succ(key_hash)
        return node.retrieve_key(key)
    
    # Reciev boradcast message
    def _reciev_broadcast(self):
        # logger.debug("recive broadcast de chord")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.bind(('', int(self.port)))
        s.bind(('', int(self.port)))

        # logger.debug(f'running _reciev_broadcast running')

        while True:
            # logger.debug(f"recive broadcast de chord in while por el puerto {self.port}!!!")
            
            msg, addr = s.recvfrom(1024)

            # logger.debug(f'Received broadcast: {self.ip}')

            msg = msg.decode().split(',')
            # logger.debug(f'received broadcast msg: {msg}')
            # logger.debug(f"recive broadcast de chord in while before try!!!")
            try:
                
                option = int(msg[0])
                # logger.debug(f"recive broadcast de chord option {option}")
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
                                # logger.debug(f'_send_data: {self.ip}')
                                s.connect((msg[2], self.port))
                                s.sendall(f'{JOIN},{self.ref}'.encode('utf-8'))
                                # logger.debug(f'_send_data end: {self.ip}')
                        except Exception as e:
                            logger.debug(f"Error sending data: {e}")
                    #TODO Enviar respuesta
                
                if option == FIND_LEADER:
                    # print("Entra al if correcto en chord")
                    # Asegúrate de que msg[1] contiene la dirección IP del cliente que hizo el broadcast
                    ip_client = msg[1].strip()  # Elimina espacios en blanco
                    response = f'{self.ip},{self.port}'.encode()  # Prepara la respuesta con IP y puerto del líder
                    # print("-----------------------------------------")
                    # print(f"enviando respuesta {response} a {(ip_client,8003)}")
                    # print("-----------------------------------------")

                    s.sendto(response, (ip_client,8003))  # Envía la respuesta al cliente
                    
                    
            except Exception as e:
                print(f"Error in _receiver_boradcast: {e}")

    # def reasign(self, new: ChordNodeReference, node: int):
    #     min = self.pred.id if node == 1 else self.id
    #     max = self.id if node == 1 else self.succ.id 
        
    #     store = self.controller.get_docs_between([-1, node], min, new.id) # llaves que tiene que guardar el actual predecesor own_pred_keys[old_predeccesro_id : new_predeccesor_id - 1]
    #     own_keys = self.controller.get_docs_between([-1, node], new.id, max)  # own_pred_keys[new_predeccesor_id : self.id - 1]
        
    #     return own_keys, store if node == 1 else store, own_keys
             

    # def stabilize_data(self, new: ChordNodeReference):
    #     keep, keep_new = self.reasign(new, 0)
        
    #     self.controller.create_doc_list(keep, -1)
    #     self.controller.create_doc_list(keep_new, 0)
        
    #     new.stabilize_data_step1(keep_new, keep)
        
    # def stabilize_data_step1(self, own, replicate):
    #     keep, keep_new = self.reasign(self.succ, 1)
    
    #     self.controller.create_doc_list(keep + own, -1)
    #     self.controller.create_doc_list(keep_new + replicate, 1)
        
    #     self.succ.stabilize_data_step2(keep_new, keep)
        
    # def stabilize_data_step2(self, own, replicate):
    #     self.controller.create_doc_list(own, -1)
    #     self.controller.create_doc_list(replicate, 1)
        
        
        
        