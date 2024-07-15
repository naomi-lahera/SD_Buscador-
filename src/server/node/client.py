import socket
import threading
import time

class Client:
    def __init__(self):
        self.port = 8002
        self.leader_ip = None
        self.leader_port = None
        self.update_leader_thread = threading.Thread(target=self.update_leader_info, daemon=True)
        self.update_leader_thread.start()

    def update_leader_info(self):
        """Actualiza la información del líder cada 5 segundos en un hilo separado."""
        while True:
            leader_ip, leader_port = self.find_leader()
            self.leader_ip, self.leader_port = leader_ip, leader_port
            time.sleep(30)

    def find_leader(self):
        # Crear un socket para enviar el broadcast con SO_REUSEADDR
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        broadcast_socket.bind(('', 8002))
        
        remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"18,{remitter_ip}, hola"
        broadcast_socket.sendto(message.encode(), ('<broadcast>', self.port))
        print("Buscando líder...")

        # Crear un socket para recibir la respuesta del líder con SO_REUSEADDR
        response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        response_socket.bind(('', 8003))
        
        try:
            response_socket.settimeout(10)  # 10 segundos de tiempo de espera
            data, addr = response_socket.recvfrom(1024)
            if data:
                leader_info = data.decode('utf-8').split(',')
                leader_ip, port = leader_info
                print(f"Líder encontrado en {leader_ip}")
                return leader_ip, int(port)
        except socket.timeout:
            print("Líder no encontrado. Cerrando el socket")
        finally:
            response_socket.close()
            broadcast_socket.close()

    def send_query_to_leader(self, query_text):
        """
        Envía una consulta al líder en el formato (20,<texto de la consulta>).
        
        Args:
        query_text (str): El texto de la consulta a enviar.
        """
        while not self.leader_ip or not self.leader_port:
            print("No se pudo encontrar al líder. Intentando en 5 segundos reenviar la consulta...")
            time.sleep(5) 
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        sock.bind(('', 8002))

        remitter_ip = socket.gethostbyname(socket.gethostname())
        message = f"20,{remitter_ip},{query_text}"
        
        print(message)
        # sock.connect((self.leader_ip, self.leader_port))
        print(f"Conectado al líder en {self.leader_ip}:{self.leader_port}")
        # sock.sendall(message.encode())
        sock.sendto(message.encode(), ('<broadcast>', self.port))
        
        print(f"Consulta enviada: {message}")
        sock.shutdown(socket.SHUT_RDWR)
        
        response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permitir reutilización del puerto
        response_socket.bind(('', 8004))
        
        try:
            response_socket.settimeout(10)  # 10 segundos de tiempo de espera
            data, addr = response_socket.recvfrom(1024)
            if data:
                data = data.decode('utf-8')
                print(f"La respuesta de la consulta fue {data}")
                return data
        except:
            print("Error al recibir la respuesta de la consulta")

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