from threading import Thread, Timer, Lock
from queue import Queue
import hashlib
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController

class Leader:
    responses_queue = Queue()
    query_states = {}
    query_states_lock = Lock()
    controller = DocumentoController("leader")
    model = Retrieval_Vectorial()

    @staticmethod
    def receive_query_from_client(chord_node, query: str, ip_client):
        hashed_query = hashlib.sha256(query.encode()).hexdigest()

        with Leader.query_states_lock:
            if hashed_query not in Leader.query_states:
                Leader.query_states[hashed_query] = {
                    "responses_list": [],
                    "timeout_timer": None,
                    "query": query
                }

        data_to_send = f'{hashed_query},{query}'
        chord_node._send_broadcast(17, data_to_send)

        wait_time = 5
        timer = Timer(wait_time, lambda: Leader.__handle_timeout(hashed_query))
        timer.start()

        with Leader.query_states_lock:
            Leader.query_states[hashed_query]["timeout_timer"] = timer

        documents = Leader.__send_answer_to_client(hashed_query)
        return ip_client, documents

    @staticmethod
    def __handle_timeout(hashed_query):
        with Leader.query_states_lock:
            if hashed_query in Leader.query_states:
                state = Leader.query_states[hashed_query]
                if state["timeout_timer"]:
                    state["timeout_timer"].cancel()

                while not Leader.responses_queue.empty():
                    state["responses_list"].append(Leader.responses_queue.get())

                print("Respuestas recibidas:", state["responses_list"])
                # Limpieza adicional si es necesario

    @staticmethod
    def __send_answer_to_client(hashed_query):
        with Leader.query_states_lock:
            state = Leader.query_states[hashed_query]
            [Leader.controller.create_document(doc) for _, doc in state["responses_list"] if _ == hashed_query]
            documents = Leader.model.retrieve(state["query"], Leader.controller, 10)
            Leader.controller.delete_all_documents()
            # Limpieza del estado de la consulta
            del Leader.query_states[hashed_query]
        return documents
        
