import socket
import threading, multiprocessing
import sys
import time
import logging
import hashlib
import logging
from node.bully import BullyBroadcastElector


# from node.leader import Leader

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

# MCAST_PORT = '8002'
# MCAST_ADRR = '224.0.0.1'

BCAST_PORT = '8006'

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
CHECK_NODE = 12
CLOSEST_PRECEDING_FINGER = 13
STORE_KEY = 14
RETRIEVE_KEY = 15
SEARCH = 16
REQUEST_BROADCAST_QUERY = 17
FIND_LEADER = 18
POW = 19
NOTIFY_PRED = 20
CHECK_SUCCESOR = 21

#------------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3
LEADER_POW = 4

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
                # if op == CHECK_NODE:
                #     s.settimeout(2)
                if op == CHECK_SUCCESOR:
                    s.settimeout(2)
                s.connect((self.ip, self.port))
                s.sendall(f'{op},{data}'.encode('utf-8'))
                return s.recv(1024)
        except Exception as e:
            print(f"Error sending data: {e}")
            return b''

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
    def successor(self) -> 'ChordNodeReference':
        response = self._send_data(GET_SUCCESSOR).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Property to get the predecessor of the current node
    @property
    def predecessor(self) -> 'ChordNodeReference':
        response = self._send_data(GET_PREDECESSOR).decode().split(',')
        return ChordNodeReference(response[1], self.port)

    # Method to notify the current node about another node
    def notify(self, node: 'ChordNodeReference'):
        # logger.debug(f'node {self.id} sending notify to {node}')
        self._send_data(NOTIFY, f'{node.id},{node.ip}')
        
    def check_succesor(self):
        return self._send_data(CHECK_SUCCESOR)
        
    # def notify_pred(self, node: 'ChordNodeReference'):
    #     self._send_data(NOTIFY_PRED, f'{node.id},{node.ip}')

    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)

    # def check_node(self):
    #     return self._send_data(CHECK_NODE)
    
    

class ChordNode():
    def __init__(self, ip: str, port: int = 8001, m: int = 4):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.succ = None
        self.pred = None
        
#____________________________________________________________OK______________________________________________________________________#
        # self.m = m # Number of bits in the hash/key spac

        # self.finger = [self.ref] * self.m  # Finger table
        # # print(f'm : {self.m}')
        # self.next = 0  # Finger table index to fix next
        
#___________________________________________________________________________________________________________________________________#

        self.e = BullyBroadcastElector()
        threading.Thread(target=self.e.loop, daemon=True).start()
        # threading.Thread(target=self.check_predecessor, daemon=True).start()
        threading.Thread(target=self.check_succesor, daemon=True).start()
        

    # Helper method to check if a value is in the range (start, end]
    def _inbetween(self, k: int, start: int, end: int) -> bool:
        if start < end:
            return start < k <= end
        else:  # The interval wraps around 0
            return start < k or k <= end

    # Internal method to send data to all nodes
    def _send_broadcast(self, op: int, data: str = None) -> bytes:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # s.sendto(f'{op},{data}'.encode(), (str(socket.INADDR_BROADCAST), self.port))
            s.sendto(f'{op},{data}'.encode(), (str(socket.INADDR_BROADCAST), int(BCAST_PORT)))
            s.close()
            # logger.debug(f'Broadcast sended')


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
        if not self.pred and not self.succ: # Existe unúnico nodo en el anillo
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
        """Join a Chord network using 'node' as an entry point."""
        self.pred = None
        # logger.debug(f'join node.find_successor {self.ip}')
        self.succ = node.find_successor(self.id)
        if self.succ:
            self.succ.notify(self.ref)

    # Method to join a Chord network without 'node' reference as an entry point
    def joinwr(self):
        self._send_broadcast(JOIN, self.ref)

    def stabilize(self):
        """Regular check for correct Chord structure."""
        while True:
            if self.succ:
                if self.succ.check_succesor() == b'':
                    time.sleep(10)
                    continue
                x = self.succ.predecessor
                if x and x.id != self.id:
                    self.succ = x
                self.succ.notify(self.ref)
                
            if not self.succ and self.pred:
                self.succ = self.pred
                
            print(f"node : {self.id} \n successor : {self.succ} predecessor {self.pred}")
            time.sleep(10)

    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        if not self.pred or self._inbetween(node.id, self.pred.id, self.id):
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

    # Reciev boradcast message
    def _receiver_broadcast(self):
        # print("recive broadcast de chord")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # s.bind(('', int(self.port)))
        s.bind(('', int(BCAST_PORT)))

        # logger.debug(f'running _reciev_broadcast running')

        while True:
            msg, addr = s.recvfrom(1024)

            # logger.debug(f'Received broadcast: {self.ip}')

            msg = msg.decode().split(',')
            # logger.debug(f'received broadcast msg: {msg}')

            try:
                option = int(msg[0])
                if option == REQUEST_BROADCAST_QUERY:
                    hashed_query, query = msg[1].split(',', 1)  # Asume que el mensaje recibido tiene la forma: hash,query
            
                    # Verifica si el mensaje es una respuesta a nuestra consulta actual
                    if hasattr(self, None) and self.hash_query == hashed_query:
                        # Pone la respuesta en la cola de respuestas del Leader
                        self.responses_queue.put(query)
                if option == JOIN:
                    if msg[2] == self.ip:
                        logger.debug(f'My own broadcast msg: node-{self.id}')
                    else:
                        new_node_ref = ChordNodeReference(msg[2])
                        new_node_ref._send_data(JOIN, {self.ref})
                
                if option == FIND_LEADER and self.ImLeader:
                    
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
                
    def find_pred(self, id: int, direction=True) -> 'ChordNodeReference':
        node = self
        if direction:
            while not self._inbetween(id, node.id, node.succ.id):
                node = node.succ
        else:
            while not self._inbetween(id, node.pred.id, node.id):
                node = node.pred
        return node
            
    # def check_predecessor(self):
    #     while True:
    #         if self.pred and self.pred.check_node() == b'':
    #             logger.debug('\n\n\n ALARMA!!! PREDECESOR PERDIDO!!! \n\n\n')
    #             self.pred = self.find_pred(self.pred.id)
    #             self.pred.notify_pred(self.ref)
    #         time.sleep(10)

    # def notify_pred(self, node: 'ChordNodeReference'):
    #     logger.debug(f'in notify_pred, my id: {self.id} my succ: {node.id}')
    #     self.succ = node
        
    def check_succesor(self):
        while True:
            if self.succ:
                logger.debug(f'succesor de {self.id} = {self.succ.id}')
            if self.succ and self.succ.check_succesor() == b'':
                logger.debug('\n\n\n ALARMA!!! SUCESOR PERDIDO!!! \n\n\n')
                if self.pred:
                    self.succ = self.pred.find_successor(self.succ.id)
                    if self.succ:
                        self.succ.notify(self.ref)
                else:
                    self.succ = self.pred = None
            time.sleep(10)

