import socket
import threading
import time
import logging

# Configuración inicial de logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)

#------------------------PUERTOS------------------------------
LEADER_REC_CLIENT = 1
LEADER_SEND_CLIENT_FIND = 2
LEADER_SEND_CLIENT_QUERY = 3
LEADER_POW = 4

CHECK_LEADER = 23

class Client:
    def __init__(self):
        self.port = 8002
        self.leader_ip = None
        self.leader_port = None
        self.update_leader_thread = threading.Thread(target=self.update_leader_info, daemon=True)
        threading.Thread(target=self.check_leader, daemon=True).start()
        self.update_leader_thread.start()

    def check_leader(self):
        while True:
            if self.leader_ip:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        print(f'check_leader: {self.leader_ip}')
                        #if op == CHECK_NODE: 
                        s.settimeout(2)
                        s.connect((self.leader_ip, self.leader_port))
                        s.sendall(f'{CHECK_LEADER}'.encode('utf-8'))
                        # logger.debug(f'_send_data end: {self.ip}')
                        s.recv(1024)
                        time.sleep(5)
                except Exception as e:
                    print('Lider caido')
                    self.leader_ip = None
                    self.leader_port = None
                    threading.Thread(target=self.update_leader_info, daemon=True).start()
                    time.sleep(5)
                    # self.update_leader_info()
                    # return b''
            
        
    def update_leader_info(self):
        """Actualiza la información del líder cada 5 segundos en un hilo separado."""
        while True:
            try:
                leader_ip, leader_port = self.find_leader()
                self.leader_ip, self.leader_port = leader_ip, leader_port
                print(f"Líder encontrado en {self.leader_ip}")
                return
                # time.sleep(4)
            except:
                print("-----No encontro el lider-------")
                time.sleep(4)

    def find_leader(self):
        # Crear un socket para enviar el broadcast con SO_REUSEADDR
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        broadcast_socket.bind(('', 8002))
        
        remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"18,{remitter_ip},hola"
        print(f"Buscando líder en {self.port} ...")
        broadcast_socket.sendto(message.encode(), ('<broadcast>', self.port))

        # Crear un socket para recibir la respuesta del líder con SO_REUSEADDR
        response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        response_socket.bind(('', 8003))
        print(f"Remitente {remitter_ip}")
        try:
            response_socket.settimeout(4)  # 10 segundos de tiempo de espera
            data, addr = response_socket.recvfrom(1024)
            if data:
                leader_info = data.decode('utf-8').split(',')
                leader_ip, port = leader_info
                print(f"Líder encontrado en {addr}")
                return leader_ip, int(port)
        except socket.timeout:
            # print("Líder no encontrado. Cerrando el socket")
            pass
        # finally:
        #     response_socket.close()
        #     broadcast_socket.close()

    def send_query_to_leader(self, query_text):
        """
        Envía una consulta al líder en el formato (20,<texto de la consulta>).

        Args:
        query_text (str): El texto de la consulta a enviar.
        """
        while not self.leader_ip or not self.leader_port:
            # print("No se pudo encontrar al líder. Intentando en 5 segundos reenviar la consulta...")
            time.sleep(5) 

        # Crear un socket TCP para enviar la consulta al líder
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        sock.bind(('', 8002))

        remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"20,{remitter_ip},{query_text}"

        # print(message)
        try:
            sock.connect((self.leader_ip, self.leader_port))  # Establecer conexión con el líder
            # print(f"Conectado al líder en {self.leader_ip}:{self.leader_port}")
            sock.sendall(message.encode())  # Enviar mensaje usando sendall para sockets TCP

            # print(f"Consulta enviada: {message}")
            sock.shutdown(socket.SHUT_RDWR)  # Indicar que no se enviarán más datos
        except Exception as e:
            # print(f"Error al enviar la consulta al líder: {e}")
            pass
        finally:
            sock.close()  # Asegurarse de cerrar el socket cuando termine

        # No es necesario recibir respuesta en este ejemplo, pero puedes agregar lógica aquí si es necesario

    # def run(self):
    #     while True:
    #         try:
    #             if self.leader_ip and self.leader_port:
    #                 print("Conectado al líder.")
    #                 # Ejemplo de envío de consulta al líder
    #                 self.send_query_to_leader("consulta de ejemplo")
                    
    #                 time.sleep(5)  # Espera antes de volver a intentar enviar otra consulta
    #         except Exception as e:
    #             print(f"Error al conectar al líder: {e}. Reintentando en 5 segundos...")
    #             threading.Timer(5, self.run).start()  # Reintentar después de 5 segundos

# # Ejemplo de uso
# c = Client()
# c.run()