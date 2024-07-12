from threading import Thread, Timer
from queue import Queue
import hashlib
# from node.chord.chord import ChordNode 

class Leader:
    responses_queue = Queue()
    timeout_timer = None
    hash_query = None
    port = None
    responses_list = []

    @staticmethod
    def set_chord_node_port(port):
        Leader.port = port

    @staticmethod
    def receive_query_from_client(chord_node, query: str):
        # Hashear la query
        hashed_query = hashlib.sha256(query.encode()).hexdigest()
        Leader.hash_query = hashed_query

        # Prepara los datos para el broadcast incluyendo la hash de la query y la query misma
        data_to_send = f'{hashed_query},{query}'
        chord_node._send_broadcast(17, data_to_send)

        # Vaciar la lista de respuestas antes de establecer un nuevo temporizador
        Leader.responses_list.clear()

        # Establece un temporizador para esperar respuestas
        wait_time = 5  # Tiempo en segundos para esperar respuestas
        Leader.timeout_timer = Timer(wait_time, Leader.__handle_timeout)
        Leader.timeout_timer.start()
        Leader.hash_query = None

    @staticmethod
    def __handle_timeout():
        # Limpia el temporizador
        if Leader.timeout_timer:
            Leader.timeout_timer.cancel()

        # Extrae todas las respuestas de la cola y las procesa
        while not Leader.responses_queue.empty():
            Leader.responses_list.append(Leader.responses_queue.get())
        print("Respuestas recibidas:", Leader.responses_list)
        # No es necesario el return aquí