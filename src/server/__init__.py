import socket
from node.node import Node
import sys
# from node.chord.chord import ChordNodeReference
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController
from node.client import Client   
# from node.chord.chord import ChordNodeReference

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    
    if len(sys.argv) >= 2 and sys.argv[1] == '-c': # -c = new client
        # Inicializa y ejecuta el cliente
        # client_ip = '172.17.2.2'
        client = Client()
        client.send_query_to_leader("I like science")
        while True:
            pass
    node = Node(Retrieval_Vectorial(),DocumentoController(ip),ip)

    # if len(sys.argv) >= 2:
    #     if sys.argv[1] == '-e':
    #         node.joinwr()
    #     elif sys.argv[1] == '-i':
    #         pass
    #     elif sys.argv[1] == '-n':
    #         if len(sys.argv) >= 3:
    #             other_ip = sys.argv[2]
    #             node.join(ChordNodeReference(other_ip, node.port))
    # print('*****************************************************')
    # print(f"IP: {ip}")
    # print(sys.argv)    
    # print('*****************************************************')

    if len(sys.argv) >= 2 and sys.argv[1] == '-n': # -n = new node
        node.joinwr()
    

    
    
    # node.add_doc("Computer Science is the most exciting place")
    # node.add_doc("Animals are beautiful")
    # node.add_doc("The documents of Alexandria were hidden for a long time")
    # print("---------------------------------------------")
    # print(node.search("Hi Nao, i like Science and animals too in any place"))
    # print("---------------------------------------------")
    
    while True:
        pass
    