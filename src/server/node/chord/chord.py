import socket
import threading
import sys
import time
import logging
import hashlib
import logging

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

MCAST_PORT = '8002'
MCAST_ADRR = '224.0.0.1'

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

# Configurar el nivel de log
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')

logger = logging.getLogger(__name__)

# # Function to hash a string using SHA-1 and return its integer representation
# def getShaRepr(data: str):
#     return int(hashlib.sha1(data.encode()).hexdigest(), 16)

def getShaRepr(data: str, max_value: int = 16):
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

    def __str__(self) -> str:
        return f'{self.id},{self.ip},{self.port}'

    def __repr__(self) -> str:
        return str(self)


class ChordNode:
    def __init__(self, ip: str, port: int = 8001, m: int = 4):
        self.id = getShaRepr(ip)
        self.ip = ip
        self.port = port
        self.ref = ChordNodeReference(self.ip, self.port)
        self.succ = None
        self.pred = None
        self.m = m # Number of bits in the hash/key spac

        self.finger = [self.ref] * self.m  # Finger table
        # print(f'm : {self.m}')
        self.next = 0  # Finger table index to fix next

        self.Leader = None
        self.mcast_adrr = MCAST_ADRR
        self.InElection = False
        self.ImTheLeader = True

        threading.Thread(target=self.stabilize, daemon=True).start()
        threading.Thread(target=self._receiver_broadcast, daemon=True).start()
        # threading.Thread(target=self.mcast_server).start()
        # threading.Thread(target=self.election_loop, daemon=True).start()
        threading.Thread(target=self.fix_fingers, daemon=True).start()  # Start fix fingers thread


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


    def mcast_call(self, message: str, mcast_addr: str, port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        s.sendto(message.encode(), (mcast_addr, port))
        s.close()

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

    # Method to find the closest preceding finger of a given id
    def closest_succeding_finger(self, id: int) -> 'ChordNodeReference':
        for i in range(self.m):
            if self.finger[i] and self._inbetween(id, self.id, self.finger[i].id):
                return self.finger[i]
        return self.ref
    
     # Method to find the closest preceding finger of a given id
    def closest_preceding_finger(self, id: int) -> 'ChordNodeReference':
        for i in range(self.m - 1, -1, -1):
            if self.finger[i] and self._inbetween(self.finger[i].id, self.id, id):
                return self.finger[i]
        return self.ref

    def find_succ(self, id: int) -> 'ChordNodeReference':
        if not self.pred: # Existe unúnico nodo en el anillo
            return self.ref

        # logger.debug(f'closest_succeding_finger de {id} : {self.closest_succeding_finger(id)}')

        if self.id < id: # Mi sucesor es mejor candidato a sucesor que yo
            if self.succ.id > self.id: # # Mi sucesor es mejor candidato a sucesor que yo
                closest_succeding_finger = self.closest_succeding_finger(id)
                # return self.succ.find_successor(id)
                return closest_succeding_finger.find_successor(id)
            else:
                return self.succ # El nodo esta entre yo y mi sucesor. El sucesor el mi sucesor
        else: # Soy candidatoa  sucesor
            if self.pred.id < self.id: # Verificacion de que soy el menor de los mayores
                if self.pred.id > id: # Mi predecesor es mejor candidato a sucesor que yo
                    closest_preceding_finger = self.closest_preceding_finger(id)
                    # return self.pred.find_successor(id)
                    return closest_preceding_finger.find_successor(id)
                else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                    return self.ref
            else: # El nodo esta entre mi predecesor y yo. Yo soy el sucesor del nodo
                return self.ref

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

            for index, node in enumerate(self.finger):
                logger.debug(f'node: {index} succesor: {node}')

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

                if option == JOIN:
                    if msg[2] == self.ip:
                        logger.debug(f'My own broadcast msg: node-{self.id}')
                    else:
                        new_node_ref = ChordNodeReference(msg[2])
                        new_node_ref._send_data(JOIN, {self.ref})
            except Exception as e:
                print(f"Error in _receiver_boradcast: {e}")


    def election_bully(self, id, otherId):
        return int(id.split('.')[-1]) > int(otherId.split('.')[-1])

    def election_call(self):
        threading.Thread(target=self.mcast_call, args=(f'{ELECTION}', MCAST_ADRR, MCAST_PORT)).start()
        print("Election Started")

    def election_winner_call(self):
        threading.Thread(target=self.mcast_call, args=(f'{ELECTION_WINNER}', MCAST_ADRR, MCAST_PORT))
        print("Elected Leadder")

    def election_loop(self):
        counter = 0
        while True:
            if not self.Leader and not self.InElection:
                self.election_call()
                self.InElection = True

            elif self.InElection:
                counter += 1
                if counter == 10:
                    if not self.Leader and self.ImTheLeader:
                        self.ImTheLeader = True
                        self.Leader = self.id
                        self.InElection = False
                        self.election_winner_call()
                    counter = 0
                    self.InElection = False

            else:
                print(f'Leader: {self.Leader}')

            print(f"{counter} waiting")
            time.sleep(1)

    def mcast_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        membership = socket.inet_aton(self.mcast_adrr) + socket.inet_aton('0.0.0.0')
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        s.bind(('', int(MCAST_PORT)))

        while True:
            try:
                msg, sender = s.recvfrom(1024)
                if not msg:
                    continue  # Ignorar mensajes vacíos

                logger.debug(f'multcast msg: {msg}')
                newId = sender[0]
                msg = msg.decode("utf-8")

                if msg.isdigit():
                    msg = int(msg)
                    if msg == ELECTION and not self.InElection:
                        print(f"Election message received from: {newId}")

                        if not self.InElection:
                            self.InElection = True
                            self.Leader = None
                            self.election_call()

                        if self.election_bully(self.id, newId):
                            s_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            s_send.sendto(f'{ELECTION_OK}'.encode(), (newId, self.port))

                    elif msg == ELECTION_OK:
                        print(f"OK message received from: {newId}")
                        if self.Leader and self.election_bully(newId, self.Leader):
                            self.Leader = newId
                        self.ImTheLeader = False

                    elif msg == ELECTION_WINNER:
                        print(f"Winner message received from: {newId}")
                        if not self.election_bully(self.id, newId) and (not self.Leader or self.election_bully(newId, self.Leader)):
                            self.Leader = newId
                            if(self.Leader != self.id):
                                self.ImTheLeader = False
                            self.InElection = False

            except Exception as e:
                print(f"Error in server_thread: {e}")