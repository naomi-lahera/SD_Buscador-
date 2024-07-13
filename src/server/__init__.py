import socket
from node.node import Node
import sys
# from logic.models.retrieval_vectorial import Retrieval_Vectorial
# from data_access_layer.controller_bd import DocumentoController

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    # node = Node(Retrieval_Vectorial(), DocumentoController(ip), ip)
    node = Node(None, None, ip)
    
    if len(sys.argv) >= 2 and sys.argv[1] == '-n': # -n = new node
        node.joinwr()
    
    
    # node.add_doc("COmputer Science is the most exciting place")
    # node.add_doc("Animals are beautiful")
    # node.add_doc("The documents of Alexandria were hidden for a long time")
    # print("---------------------------------------------")
    # print(node.search("Hi Nao, i like Science and animals too in any place"))
    # print("---------------------------------------------")
    
    while True:
        pass
    