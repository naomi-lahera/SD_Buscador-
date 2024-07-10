import os
import sqlite3
from joblib import load, dump
from controller_bd import DocumentoController
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from src.server.logic.build.preprocessing_data.preprocess import prepro
from gensim.similarities import MatrixSimilarity
from typing import List

class Nodo():
    def __init__(self):

        read_or_create_db()
        self.controller = DocumentoController()    

    def retrieval(self, query):
        id_tf_documents = self.controller.get_documents_for_query()
        
        # Crear un diccionario y corpus para el modelo TF-IDF
        dictionary = self.controller.dictionary
        corpus:List = [bow for _, bow in id_tf_documents]
        # Convertir las cadenas a listas de Python
        listas_convertidas = [[eval(item)] for item in corpus]

        # Aplanar la lista
        corpus = [item for sublist in listas_convertidas for item in sublist]

        
        print("-----------------------------------")
        print(corpus)
        print("-----------------------------------")
        model = TfidfModel(corpus)  # fit model
        
        # Tokenizar y convertir la consulta a BoW
        prep_query = prepro.tokenize_corpus([query])[0]
        query_bow = dictionary.doc2bow(prep_query)
        # Calcular el TF-IDF para la consulta en relación con cada documento
        query_tfidf = model[query_bow]
        
        # Crear un índice de similitud a partir del corpus TF-IDF
        index = MatrixSimilarity(model[corpus])
        
        # Calcular la similitud de la consulta con cada documento
        sims = index[query_tfidf]
        
        # Encontrar el índice del documento con la mayor similitud
        max_sim_index = sims.argmax()
        
        # Obtener el ID del documento más relevante
        most_relevant_doc_id = id_tf_documents[max_sim_index][0]
        document = self.controller.get_document_by_id(most_relevant_doc_id)
        
        return document
        
def read_or_create_db():
    
    if os.path.exists('database.db'):
        "La base de datos ya existe"
        return 
    else:
        conexion = sqlite3.connect('database.db')
    
        cursor = conexion.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
        	id INTEGER PRIMARY KEY,
        	texto_documento TEXT NOT NULL,
        	tf TEXT
        );
        ''')
        conexion.commit()
        conexion.close()
        print("La base de datos se creó correctamente")

    
     
nodo = Nodo()
# nodo.controller.create_document("Hi my name is leo")
# nodo.controller.create_document("The air is fluid charming today")
# nodo.controller.create_document("Computer Science is a big dream")
# nodo.controller.create_document("Italy is a country from Asia")
# print(nodo.controller.get_documents())
# print("----------------------------------")
# nodo.controller.update_document(4,"Italy is a country from Europe")
# print(nodo.controller.get_documents())
# print("----------------------------------")

# nodo.controller.delete_document(2)
# print(nodo.controller.get_documents())
# print("----------------------------------")

# nodo = Nodo()
# print(nodo.retrieval("the big dream now"))  
print(nodo.retrieval("Hi Leo leo"))  
