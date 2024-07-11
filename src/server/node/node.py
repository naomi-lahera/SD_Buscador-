from node.chord.chord import ChordNode, ChordNodeReference
import threading
import socket
from logic.core.doc import document
from typing import List
import os
import sqlite3
from joblib import load, dump
from src.server.data_access_layer.controller_bd import DocumentoController
from src.server.logic.models.retrieval_vectorial import Retrieval_Vectorial

# from data_access_layer.grocer_tfidf_joblib import grocer_vectorial_model_joblib

import logging

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
CHECK_PREDECESSOR = 6
CLOSEST_PRECEDING_FINGER = 7
STORE_KEY = 8
RETRIEVE_KEY = 9
JOIN = 10
SEARCH = 11

def read_or_create_db():
    
    if os.path.exists('database.db'):
        "La base de datos ya existe"
        return 
    else:
        conexion = sqlite3.connect('database.db')
    
        cursor = conexion.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
        	id INTEGER PRIMARY KEY,
        	texto_documento TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        conexion.commit()
        conexion.close()
        print("La base de datos se creó correctamente")    

class Node(ChordNode):    
    def __init__(self, ip: str, port: int = 8001, m: int = 160,controller = DocumentoController(),model = Retrieval_Vectorial()):
        read_or_create_db()
        super().__init__(ip, port, m)
        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        self.controller = controller
        self.model = model    
    
    def search(self, query) -> List[document]:
        # return grocer_vectorial_model_joblib.get_docs_query(query)[:5]
        self.model.retrieval(query,self.controller)
    
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
                # elif option == SEARCH:
                #     query = data[1]
                #     data_resp = self.search(query)
                elif option == JOIN:
                    # logger.debug(f'JOIN data msg : {data[0]} - {self.ip}')
                    chord_node_ref = ChordNodeReference(data[2])
                    if chord_node_ref:
                        logger.debug(f'join to the chord network - {self.ip}')
                        # logger.debug(f'I have the chord node ip to for join to the chord network : {self.ip}')
                        logger.debug(f'node_reference - {chord_node_ref.ip}')
                        self.join(chord_node_ref)
                    
                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()