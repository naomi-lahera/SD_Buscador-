import socket
from node.chord.chord import ChordNodeReference
from node.node import Node
import sys

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    node = Node(ip)

    if len(sys.argv) >= 2:
        # other_ip = sys.argv[1]
        # node.join(ChordNodeReference(other_ip, node.port))
        
        node.join_wr()
    
    while True:
        pass