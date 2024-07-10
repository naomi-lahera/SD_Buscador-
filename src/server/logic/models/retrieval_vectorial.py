from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from src.server.logic.build.preprocessing_data.preprocess import prepro
from gensim.similarities import MatrixSimilarity
from typing import List
from src.server.data_access_layer.controller_bd import DocumentoController

class Retrieval_Vectorial():
    def __init__():
        pass
    def retrieval(self, query,controller:DocumentoController):
        id_tf_documents = controller.get_documents_for_query()
        
        # Crear un diccionario y corpus para el modelo TF-IDF
        dictionary = controller.dictionary
        corpus:List = [bow for _, bow in id_tf_documents]
        # Convertir las cadenas a listas de Python
        listas_convertidas = [[eval(item)] for item in corpus]

        # Aplanar la lista
        corpus = [item for sublist in listas_convertidas for item in sublist]

        model = TfidfModel(corpus)  # fit model
        
        # Tokenizar y convertir la consulta a BoW
        prep_query = prepro.tokenize_corpus([query])[0]
        query_bow, missings = dictionary.doc2bow(prep_query,return_missing=True)
        
        # Inicializa un contador para los términos faltantes
        missing_count = {}

        # Itera sobre el BoW para identificar y contar los términos faltantes
        print(dictionary.token2id)
        for term_id, freq in missings.items():
            if term_id not in dictionary.token2id:
                missing_count[term_id] = freq

        # Agrega los términos faltantes al BoW con un recuento de 0
        for term_id, freq in missing_count.items():
            query_bow.append((term_id, freq))
            
        # Calcular el TF-IDF para la consulta en relación con cada documento
        print(query_bow)
        query_tfidf = model[query_bow]
        
        # Crear un índice de similitud a partir del corpus TF-IDF
        index = MatrixSimilarity(model[corpus])
        
        # Calcular la similitud de la consulta con cada documento
        sims = index[query_tfidf]
        
        # Encontrar el índice del documento con la mayor similitud
        max_sim_index = sims.argmax()
        
        # Obtener el ID del documento más relevante
        most_relevant_doc_id = id_tf_documents[max_sim_index][0]
        document = controller.get_document_by_id(most_relevant_doc_id)
        
        return document