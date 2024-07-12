import socket
from node.node import Node
import sys
from node.chord.chord import ChordNodeReference
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    node = Node(Retrieval_Vectorial(),DocumentoController(),ip)

    if len(sys.argv) >= 2:
        if sys.argv[1] == '-e':
            node.joinwr()
        elif sys.argv[1] == '-i':
            pass
        elif sys.argv[1] == '-n':
            if len(sys.argv) >= 3:
                other_ip = sys.argv[2]
                node.join(ChordNodeReference(other_ip, node.port))
    
    while True:
        pass