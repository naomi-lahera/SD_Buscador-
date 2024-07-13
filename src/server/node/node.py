from node.chord.chord import ChordNode, ChordNodeReference
import threading
import socket
from logic.core.doc import document
from typing import List
import os
import sqlite3
from logic.models.model_interface import ModelSearchInterface
from data_access_layer.controller_interface import BaseController

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

def read_or_create_db(ip):
    ip = str(ip)
    folder_path = 'src/server/data/nodes_data/'
    full_path = os.path.join(folder_path, ip)
    
    if os.path.exists(f"{full_path}/database.db"):
        print("El nodo ya existia")
        return 
    
    else:
        # os.makedirs(full_path)
        # print(f"Carpeta creada en: {full_path}")
        try:
            conexion = sqlite3.connect(os.path.join(full_path, 'database.db'))
            print("Conexión a la base de datos exitosa")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
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
        print("La base de datos se creó correctamente")    

class Node(ChordNode):    
    def __init__(self, model:ModelSearchInterface, controller:BaseController, ip: str):
        read_or_create_db(ip)
        
        super().__init__(ip)
        self.controller:BaseController = controller
        self.model = model    

        threading.Thread(target=self.start_server, daemon=True).start()  # Start server thread
        
    
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
    
    def search(self, query) -> List[document]:
        return self.model.retrieve(query,self.controller)
    
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
                elif option == JOIN and not self.succ:
                    ip = data[2]
                    self.join(ChordNodeReference(ip, self.port))
                    
                if data_resp:
                    response = f'{data_resp.id},{data_resp.ip}'.encode()
                    conn.sendall(response)
                conn.close()