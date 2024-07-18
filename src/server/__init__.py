import socket
from node.node import Node
import sys
# from node.chord.chord import ChordNodeReference
from logic.models.retrieval_vectorial import Retrieval_Vectorial
from data_access_layer.controller_bd import DocumentoController
from node.client import Client   
import time
# from node.client import Client   
# from node.chord.chord import ChordNodeReference

if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Devuelve : {ip}")
    
    if len(sys.argv) >= 2 and sys.argv[1] == '-c': # -c = new client
        # Inicializa y ejecuta el cliente
        # client_ip = '172.17.2.2'
        client = Client()
        def adding():
            client.insert_to_leader("""172.17.0.2""")
            time.sleep(2)
            client.insert_to_leader("""172.17.0.3""")
            time.sleep(2)
            client.insert_to_leader("""172.17.0.4""") # ,'172.17.0.3'
            time.sleep(2) 
            client.insert_to_leader("""172.17.0.5""") # '172.17.0.4'
            time.sleep(2)
          
        def adding2():
            client.insert_to_leader("""
                                         Science is the systematic and logical approach to discovering how things
                                         in the universe work. 
                                         """)
            time.sleep(2)
            client.insert_to_leader("""This paper is so shit.""")
            time.sleep(2)
            client.insert_to_leader("""
                                        Hi i am not a of science encompasses various disciplines, each focusing on different aspects
                                         """) # ,'172.17.0.3'
            time.sleep(2) 
            client.insert_to_leader("""
                                        of the world around us. From biology exploring life forms to physics science investigating the fundamental
                                        """) # '172.17.0.4'
            time.sleep(2)
            client.insert_to_leader("""
                                       GUARAPO IS A COOL FACTOR IN THE NIGHT
                                        """) # ,'172.17.0.4'
            time.sleep(2)
            client.insert_to_leader("""
                                       the important of science becomes true
                                        """) # ,'172.17.0.5
            time.sleep(2)
             
        adding()
        adding2()
        # print('Borrando documento con id 11')
        # client.delete(0)
        # client.update(1, 'NAOMI')
        # client.delete(11)
        
#       client.send_insert_to_node("""
#                                   The integration of technologies into home voice devices, specifically Amazon Alexa, is explored to predict flight delays. This innovative approach seeks to simplify and personalize the travel experience for users, providing them with accurate information about potential delays before they occur, which can be crucial for planning their activities.
# Machine Learning techniques are used to analyze large volumes of historical data related to flights, including weather data, flight schedules, and delay statistics. Once the models are trained, they integrate with Amazon Alexa, allowing users to request delay predictions simply using voice commands.
#                                    """,'172.17.0.3')
#         time.sleep(2)
        
#         client.send_insert_to_node("""
#                                    It addresses the challenge of predicting the propagation of flight delays using deep learning techniques. This study focuses on understanding how delays in one flight can affect other connected flights in an air network. The main objective is to develop a model that can accurately predict the propagation of flight delays. This involves not only predicting whether a specific flight will be delayed, but also how widely that delay could spread to other connected flights.
# A CNN model composed of several hidden layers that process the input data to generate predictions about delay propagation is described. The model is capable of capturing complex patterns and non-linear relationships in the data.
#                                     """,'172.17.0.3')
#         time.sleep(2)
        
        
        # client.send_insert_to_node("""This paper is so shit.""",'172.17.0.3')
        # client.send_insert_to_node("172.17.0.2")
        # client.send_insert_to_node("172.17.0.3",'172.17.0.3')
        # client.send_insert_to_node("172.17.0.4",'172.17.0.4')
        # client.send_insert_to_node("172.17.0.5",'172.17.0.5')
        # time.sleep(3)
        # client.send_query_to_leader("science")
        # time.sleep(60)
        # client.send_query_to_leader("science")
        # time.sleep(60)
        # client.send_query_to_leader("science")
        # time.sleep(60)
        # client.send_query_to_leader("science")
        
        
        
        # for i in range(3):
        #     client.send_query_to_leader("I like science")
        #     time.sleep(2)
            
    elif len(sys.argv) == 1:
        node = Node(ip)
        
    elif len(sys.argv) >= 2 and sys.argv[1] == '-n': # -n = new node
        
        node = Node(ip)
        node.join_CN()
        
    
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

    
    # try:
    #     node.add_doc(
    #         """
    #         Android Studio, including the binaries in this folder, is licensed to
    #         you under the Android Software Development Kit License Agreement
    #         (available at https://developer.android.com/studio/terms) and you may
    #         not copy (except for backup purposes), modify, adapt, redistribute,
    #         decompile, reverse engineer, disassemble, or create derivative works
    #         of the binaries or use the binaries separately from your use of
    #         Android Studio. 
    #         """
    #         )
    #     node.add_doc(
    #         """
    #         The ANTLR v3.1 .NET Runtime Library extend the ANTLR language processing 
    #         tools generator to the C#/CLI platforms such as Microsoft .NET, 
    #         Novell/Ximian Mono and dotGNU. It is written in the C# programming language 
    #         and was designed specifically for use with the ANTLR C# Code Generation
    #         target but, it would work equally well with a VB.NET, C++/CLI or indeed 
    #         IronPython code generator were such a thing to be developed for ANTLR v3.1.
# 
    #         We hope you find the ANTLR v3.1 .NET Runtime Library delightful and useful 
    #         even but, as per the license under which you may use it, this software is not 
    #         guaranteed to work.
    #         """
    #         )
    #     node.add_doc(
    #         """
    #         3. USING The ANTLR v3.1 .NET Runtime Library
# 
    #         Tou use the ANTLR v3.1 .NET Runtime Library in your projects, add a 
    #         reference to the following file in your projects:
    #           - Antlr3.Runtime.dll
# 
    #         If you are using StringTemplate out in your grammar, add the following 
    #         files too:  
    #           - StringTemplate.dll 
    #           - antlr.runtime.dll
# 
    #         You can find examples of using ANTLR v3.1 and the ANTLR v3.1 .NET Runtime 
    #         Library at:
    #           http://www.antlr.org/download/examples-v3.tar.gz
    #         """
    #         )
    #     node.add_doc("Computer Science is the most exciting place")
    #     node.add_doc("Animals are beautiful")
    #     node.add_doc("The documents of Alexandria were hidden for a long time")
    # except Exception as e:
    #     print(f'Error: {e}')
        
        # print("---------------------------------------------")
        # print(node.search("Hi Nao, i like Science and animals too in any place"))
        # print("---------------------------------------------")
    
    while True:
        pass
