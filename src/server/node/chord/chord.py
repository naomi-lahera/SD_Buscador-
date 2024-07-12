import socket
import threading
import sys
import time
import logging
import hashlib
import logging

from node.leader import Leader

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

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
# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

# # Function to hash a string using SHA-1 and return its integer representation
# def getShaRepr(data: str):
#     return int(hashlib.sha1(data.encode()).hexdigest(), 16)

def getShaRepr(data: str, max_value: int = 16):
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
        self.port = port

    # Internal method to send data to the referenced node
    def _send_data(self, op: int, data: str = None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
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
        logger.debug(f'node {self.id} sending notify to {node}')
        self._send_data(NOTIFY, f'{node.id},{node.ip}')

    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)


class ChordNode():
    def __init__(self, ip: str, port: int = 8001, m: int = 4):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.succ = None
        self.pred = None
        self.m = m # Number of bits in the hash/key spac
        
        self.finger = [self.ref] * self.m  # Finger table
        self.next = 0  # Finger table index to fix next
        
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.stabilize, daemon=True).start()
        threading.Thread(target=self._receiver_broadcast, daemon=True).start()
        # threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread
        
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
            s.sendto(f'{op},{data}'.encode(), (str(socket.INADDR_BROADCAST), self.port))
            s.close()
            logger.debug(f'Broadcast sended')
        
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

    # # Method to find the closest preceding finger of a given id
    # def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
    #     for i in range(self.m - 1, -1, -1):
    #         if self.finger[i] and self._inbetween(self.finger[i].id, self.id, id):
    #             return self.finger[i]
    #     return self.ref

    def find_succ(self, id: int) -> 'ChordNodeReference':
        if not self.pred: # Existe unúnico nodo en el anillo
            return self.ref
        
        if self.id < id: # Mi sucesor es mejor candidato a sucesor que yo
            if self.succ.id > self.id: # # Mi sucesor es mejor candidato a sucesor que yo
                return self.succ.find_successor(id)
            else:
                return self.succ # El nodo esta entre yo y mi sucesor. El sucesor el mi sucesor
        else: # Soy candidatoa  sucesor
            if self.pred.id < self.id: # Verificacion de que soy el menor de los mayores
                if self.pred.id > id: # Mi predecesor es mejor candidato a sucesor que yo
                    return self.pred.find_successor(id)
                else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                    return self.ref
            else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                return self.ref

    # def find_pred(self, id: int) -> 'ChordNodeReference':
    #     logger.debug(f'find pred de {id}')
    #     if not self.succ: # or self.succ.id == self.id:
    #         logger.debug(f'find pred de {id}. Hay solo un nodo, yo {self.ip} soy el predecesor')
    #         return self.ref
    #     if self._inbetween(id, self.id, self.succ.id):
    #     #if id >= self.id and id < self.succ.id: # or self.succ.id < self.id
    #         logger.debug(f'El nodo esta entre mi sucesor y yo. Yo soy su predecesor')
    #         return self.ref
    #     logger.debug(f'El sucesor de nodo esta lejos de mi. Mi sucesor {self.succ.ip} buscara el sucesor de {id}')
    #     return self.succ.find_pred(id) if id > self.id else self.pred.find_pred()
    
    # def find_pred(self, id: int) -> 'ChordNodeReference':
    #     # if not self.pred:
    #     #     return self.ref
    #     pass
        
    def join(self, node: 'ChordNodeReference'):
        """Join a Chord network using 'node' as an entry point."""
        self.pred = None
        logger.debug(f'join node.find_successor {self.ip}')
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
                x = self.succ.predecessor
                if x.id != self.id:
                    self.succ = x
                self.succ.notify(self.ref)
            if not self.succ and self.pred:
                self.succ = self.pred
            print(f"node : {self.id} \n successor : {self.succ} predecessor {self.pred}")
            time.sleep(10)
    
    # Notify method to inform the node about another node
    def notify(self, node: 'ChordNodeReference'):
        # if node.id == self.id:
        #     pass
        if not self.pred or self._inbetween(node.id, self.pred.id, self.id):
            self.pred = node
            
    # Fix fingers method to periodically update the finger table
    def fix_fingers(self):
        while True:
            try:
                for node_index in range(len(self.finger)):
                    self.finger[node_index] = self.find_succ((self.id + 2**node_index) % 2**self.m)
            except Exception as e:
                print(f"Error in fix_fingers: {e}")
                
            # for node in self.finger:
            #     logger.debug(node)
                
            time.sleep(10)
            
    # Reciev boradcast message 
    def _receiver_broadcast(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', int(self.port)))
        
        # logger.debug(f'running _reciev_broadcast running')
        
        while True:
            msg, _ = s.recvfrom(1024)
            
            logger.debug(f'Received broadcast: {self.ip}')
            
            msg = msg.decode().split(',')
            logger.debug(f'received broadcast msg: {msg}')
            
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
            except Exception as e:
                print(f"Error in _receiver_boradcast: {e}")
                

    # def start_server(self):
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #         s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #         print(self.ip, self.port)
    #         s.bind((self.ip, self.port))
    #         s.listen(10)

    #         while True:
    #             conn, addr = s.accept()
    #             print(f'new connection from {addr}' )
    #             data = conn.recv(1024).decode().split(',')
    #             # logger.debug(f'{self.ip} : datos recibidos de {addr}')

    #             data_resp = None
    #             option = int(data[0])
    #             # logger.debug(f'Opción: {option}')

    #             if option == FIND_SUCCESSOR:
    #                 id = int(data[1])
    #                 data_resp = self.find_succ(id)
    #             elif option == FIND_PREDECESSOR:
    #                 id = int(data[1])
    #                 data_resp = self.find_pred(id)
    #             elif option == GET_SUCCESSOR:
    #                 data_resp = self.succ if self.succ else self.ref
    #             elif option == GET_PREDECESSOR:
    #                 data_resp = self.pred if self.pred else self.ref
    #             elif option == NOTIFY:
    #                 ip = data[2]
    #                 self.notify(ChordNodeReference(ip, self.port))
    #             elif option == INSERT_NODE:
    #                 id = int(data[1])
    #                 ip = data[2]
    #                 self.insert_node(ChordNodeReference(ip, self.port))
    #             elif option == REMOVE_NODE:
    #                 id = int(data[1])
    #                 self.remove_node(id)
                    
    #             elif option == JOIN and not self.succ:
    #                 ip = data[2]
    #                 self.join(ChordNodeReference(ip, self.port))

    #             if data_resp:
    #                 response = f'{data_resp.id},{data_resp.ip}'.encode()
    #                 conn.sendall(response)
    #             conn.close()

# if __name__ == "__main__":
#     other_node = None
#     # if len(sys.argv) <= 1:
#     #     raise SystemError("node id is required")
#     # id = int(sys.argv[1])
#     ip = socket.gethostbyname(socket.gethostname())
#     t = ChordNode(ip)
    
#     if len(sys.argv) >= 2 and sys.argv[1] == '-n': # -n = new node
#         t.joinwr()
        
#     while True:
#         pass