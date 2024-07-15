import socket
import threading
from queue import Queue
import hashlib
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController

class LeaderNode:
    responses_queue = Queue()
    query_states = {}
    query_states_lock = threading.Lock()

    def __init__(self, ip='localhost', port=8002):
        print("[[[[[[[[[[[[[[[[[[[[[[[Creando el Leader...]]]]]]]]]]]]]]]]]]]]]]]")
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen()
        print(f"Líder escuchando en {self.ip}:{self.port}")

    def listen_for_broadcast(self):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        broadcast_socket.bind(('', self.port))

        while True:
            message, client_address = broadcast_socket.recvfrom(1024)
            print(f"Broadcast recibido de {client_address}: {message.decode('utf-8')}")
            # Aquí podrías verificar si el mensaje es una solicitud de conexión y responder al cliente con la dirección del líder.

    def listen_for_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Conexión de {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        print(f"Solicitud recibida: {request}")
        # Procesa la solicitud y envía una respuesta al cliente.
        client_socket.sendall(b"Solicitud recibida")
        client_socket.close()

    def receive_query_from_client(self, chord_node, query: str, ip_client: str):
        hashed_query = hashlib.sha256(query.encode()).hexdigest()

        with LeaderNode.query_states_lock:
            if hashed_query not in LeaderNode.query_states:
                LeaderNode.query_states[hashed_query] = {
                    "responses_list": [],
                    "timeout_timer": None,
                    "query": query
                }

        data_to_send = f'{hashed_query},{query}'
        chord_node._send_broadcast(17, data_to_send)

        wait_time = 5
        timer = threading.Timer(wait_time, lambda: LeaderNode.__handle_timeout(hashed_query))
        timer.start()

        with LeaderNode.query_states_lock:
            LeaderNode.query_states[hashed_query]["timeout_timer"] = timer

        documents = LeaderNode.__send_answer_to_client(hashed_query, ip_client)
        return ip_client, documents

    @classmethod
    def __handle_timeout(cls, hashed_query):
        with cls.query_states_lock:
            if hashed_query in cls.query_states:
                state = cls.query_states[hashed_query]
                if state["timeout_timer"]:
                    state["timeout_timer"].cancel()

                while not LeaderNode.responses_queue.empty():
                    state["responses_list"].append(LeaderNode.responses_queue.get())

                print("Respuestas recibidas:", state["responses_list"])
                # Limpieza adicional si es necesario

    @classmethod
    def __send_answer_to_client(cls, hashed_query, ip_client):
        with cls.query_states_lock:
            state = cls.query_states[hashed_query]
            controller = DocumentoController(f"leader/{ip_client}")
            model = Retrieval_Vectorial()
            [controller.create_document(doc) for _, doc in state["responses_list"] if _ == hashed_query]
            documents = model.retrieve(state["query"], controller, 10)
            controller.delete_all_documents()
            # Limpieza del estado de la consulta
            del cls.query_states[hashed_query]
        return documents

    def run(self):
        threading.Thread(target=self.listen_for_broadcast, daemon=True).start()
        self.listen_for_clients()
