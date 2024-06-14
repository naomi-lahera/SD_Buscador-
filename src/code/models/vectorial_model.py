from models.model_interface import model_interface
from build_data.preprocessing_data.preprocess import prepro 
from core.doc import document, doc_content 
from gensim.matutils import corpus2dense
from gensim.models import TfidfModel
from gensim.corpora import Dictionary
from numpy import dot
from numpy.linalg import norm

class vectorial_model(model_interface):
    def retrieve_documents(tfidf_model_object: TfidfModel, reduction_model, corpus_tfidf_dense: dict[int, document] , dictionary: Dictionary, query_text: str):
        """
        Gets the similarity between the corpus and a query

        Args:
        - tfidf_model_object : TfidfModel class from gensim.models. represent the model fited with the documents in the stock.
        - corpus_tfidf_dense : dict(int, document). Represents the documents in the corpus (id, document).
        - dictionary : Dictionary class from gensim.corpora. Represent the corpus by vocabulary and an id for every word in the vocabulary.
            tf-idf representation of the query. Each row is considered a document.
        - query_text : str. Represents the query.

        Return:
        - [doc_content]. doc_conteng -> title, text from a doc

        """
        #? OJO Todos los parametros de la funcion son parametros y no atributos de la clase xq pueden variar al insertar un nuevo documento. Por esto se cargan
        #? todos estos elementos cada vez que se hace un aquery 
        
        # precission = 0.7
        precission = 0.02
        
        # Generar el vector de la query
        tokenized_query = prepro.tokenize(query_text)
        # print('tokenized_query: ', tokenized_query)
        
        query_vector = corpus2dense([tfidf_model_object[dictionary.doc2bow(tokenized_query)]], dictionary.num_pos, 1).T
        # reducir dimensiones del vector query
        query_vector = reduction_model.transform(query_vector)
        # print('query_vector: ', query_vector[0])
        
        simils = dict()
        for id, doc in corpus_tfidf_dense.items():   
            simils[id] = vectorial_model.cosine_similarity(doc.doc_tfidf_dense, query_vector[0])

        ranked = dict(sorted(simils.items(), key=lambda item: item[1], reverse=True))
        # print('ranked: ', ranked)
        return [
            corpus_tfidf_dense[k].content 
            for k, v in ranked.items() 
            if v >= precission
            ]

    @staticmethod
    def cosine_similarity(vector, q_vector):
        # print('cosine_similarity')
        # print('vector: ', vector)
        # print('q_vector: ', q_vector)
        
        # print(0 if norm(vector) * norm(q_vector) == 0 else dot(vector, q_vector)/norm(vector) * norm(q_vector))
        
        return 0 if norm(vector) * norm(q_vector) == 0 else dot(vector, q_vector)/norm(vector) * norm(q_vector)
        
        # if norm(vector) * norm(q_vector) == 0:
        #     print('Norma cero')