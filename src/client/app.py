import streamlit as st
# from lib.utils import Chatbot, VectorStore
from pypdf import PdfReader
import logging
import joblib

logging.basicConfig(level=logging.DEBUG,
                    format='%(threadName)s - %(message)s')
logger = logging.getLogger(__name__)


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
#------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3
LEADER_POW = 4
#------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3
LEADER_POW = 4

CHECK_LEADER = 23

import socket

class Client:
    
    #_instance = None
    # history = None
    # _notified_agents = set()
    # _agreed_agents = set()

    # def __new__(cls):
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #         cls._instance.history = []  # Set the history
    #     return cls._instance
    
    def __init__(self):
        self.port = 8002
        try:
            history = joblib.load('instance.joblib')
            self.history = history
            self.query = ''
            print('loaded instance')
        except:
            self.history = []
            self.query = ''
            joblib.dump(self.history, 'instance.joblib')
            print("New instance")


    def send_broadcast_message(self, message):
        """
        Envía un mensaje por broadcast al puerto especificado.

        Args:
        message (str): El mensaje a enviar.
        """
        # Crear un socket UDP para enviar el mensaje por broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Permitir broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto

        try:
            # Enviar el mensaje por broadcast al puerto 8002
            sock.sendto(message.encode(), ('<broadcast>', 8002))
        except Exception as e:
            print(f"Error al enviar el mensaje por broadcast: {e}")
        finally:
            sock.close()

    def send_query_to_leader(self, query_text):
        """
        Envía una consulta al líder en el formato (20,<texto de la consulta>) usando broadcast.

        Args:
        query_text (str): El texto de la consulta a enviar.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Permitir broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        sock.bind(('', 8004))  # Enlazar el socket en el puerto 8004 para recibir respuestas
        
        remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"20,{remitter_ip},{query_text}"

        self.send_broadcast_message(message)
        
        sock.settimeout(3)
        
        response = None
        try:
            message, addr = sock.recvfrom(1024)
            print(f"Mensaje recibido: {message.decode('utf-8')} desde {addr}")
            response = message.decode('utf-8')
            self.query = ''
            
            self.history.append((query_text, response))
            joblib.dump(self.history, 'history.joblib')
            
            
        except socket.timeout:
            print("No se recibió respuesta en tiempo.")
        finally:
            sock.close()
            
        return response if response else None 
        
        
    def send_insert_to_node(self, query_text,id = '172.17.0.2'):
      
        # Crear un socket TCP para enviar la consulta al líder
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        sock.bind(('', 8002))

        # remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"{INSERT},documentos,{query_text}"

        # print(message)
        try:
            sock.connect((id, 8001))  # Establecer conexión con el líder
            # print(f"Conectado al líder en {self.leader_ip}:{self.leader_port}")
            sock.sendall(message.encode())  # Enviar mensaje usando sendall para sockets TCP

            # print(f"Consulta enviada: {message}")
            sock.shutdown(socket.SHUT_RDWR)  # Indicar que no se enviarán más datos
        except Exception as e:
            # print(f"Error al enviar la consulta al líder: {e}")
            pass
        finally:
            sock.close()  # Asegurarse de cerrar el socket cuando termine
#________________________________________________Streamlit__________________________________________#

st.set_page_config(page_title="The PDF Bot", page_icon="📚")

init_text = """
<div style="text-align: center;">
<h3> Hi 👋 !!! We are ciberdist 🤖 and we want you to enjoy our app. </h1>
</div
"""
st.markdown(init_text, unsafe_allow_html=True)

st.markdown("""<div style="text-align: center;"<small>Go aehead</small></div>""", unsafe_allow_html=True)

fp = st.sidebar.file_uploader("Upload a PDF file", "pdf")

if fp:
    st.write("Uploaded text")
    # st.stop()
    
client = Client()

# @st.cache_data(show_spinner="Indexing PDF...")
# def get_store(pdf):
#     # store = VectorStore()
#     store = []
#     texts = [page.extract_text() for page in PdfReader(pdf).pages]
#     store.append(texts)
#     return store

# store = get_store(fp)
# st.sidebar.write(f"Index size: {len(store)} pages.")

# USER_PROMPT = """
# The following is a relevant extract of a PDF document
# from which I will ask you a question.

# ## Extract

# {extract}

# ## Query

# Given the previous extract, answer the following query:
# {input}
# """

# # bot = Chatbot("open-mixtral-8x7b", user_prompt=USER_PROMPT)

# if st.sidebar.button("Reset conversation"):
#     # bot.reset()
#     pass

# # for message in bot.history():
# #     with st.chat_message(message.role):
# #         st.write(message.content)

msg = st.chat_input()

if msg:
    response = client.send_query_to_leader(msg)
    st.warning(response if response else 'We have no response')

# with st.chat_message("user"):
#     st.write(msg)

# # extract = store.search(msg, 3)

# # with st.chat_message("assistant"):
# #     st.write_stream(bot.submit(msg, context=2, extract="\n\n".join(extract)))


