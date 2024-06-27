from node.chord.chord import ChordNode, ChordNodeReference
import threading
import socket
from logic.core.doc import document
from typing import List
from data_access_layer.grocer_tfidf_joblib import grocer_vectorial_model_joblib

# Operation codes
FIND_SUCCESSOR = 1
FIND_PREDECESSOR = 2
GET_SUCCESSOR = 3
GET_PREDECESSOR = 4
NOTIFY = 5
CHECK_PREDECESSOR = 6
CLOSEST_PRECEDING_FINGER = 7
STORE_KEY = 8
RETRIEVE_KEY = 9
SEARCH = 10

class Node(ChordNode):    
    def __init__(self, ip: str, port: int = 8001, m: int = 160):
        super().__init__(ip, port, m)
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
    
    def search(self, query) -> List[document]:
        return grocer_vectorial_model_joblib.get_docs_query(query)[:5]
    
    # Start server method to handle incoming requests
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen(10)

            while True:
                conn, addr = s.accept()
                print(f'new connection from {addr}')

                data = conn.recv(1024).decode().split(',')

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
                elif option == NOTIFY:
                    id = int(data[1])
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

                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()