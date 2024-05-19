from gensim import models
# Para generar la matriz densa de tf-idf
from gensim.matutils import corpus2dense
from info.save_info import save_file, load_file
from preprocessing_data.preprocess import prepro 

class vectorial_model():
    def __init__(self, corpus_bow, tokenized_docs, dictionary):
        self.tokenized_docs = tokenized_docs
        self.dictionary = dictionary
        self.vocabulary = list(self.dictionary.token2id.keys())
        
        self.tfidf = models.TfidfModel(corpus_bow)
        try:
            load_file('./../../data/models/vectoral_model', 'corpus_tfidf_dense')
        except:
            self.corpus_tfidf_dense = corpus2dense(self.tfidf[corpus_bow], len(self.vocabulary) , len(self.tokenized_docs)).T
            save_file(self.corpus_tfidf_dense, './../../data/models/vectoral_model', 'corpus_tfidf_dense')
        
    def get_tfidf(self, corpus_bow):
        return self.tfidf[corpus_bow]
    
    def retrieve_documents(self, query_text):
        
        """
        Gets the similarity between the corpus and a query

        Args:
        - corpus_matriz : [[float]]
            tf-idf representation of the query. Each row is considered a document.
        - vector_query : [float]
            tf-idf representation of the query.

        Return:
        - [(int, float)]

        """
        pr = prepro()
        # Generar el vector de la query
        tokenized_query = pr.tokenize(query_text)
        query_vector = corpus2dense([self.tfidf[self.dictionary.doc2bow(tokenized_query)]], len(self.vocabulary),1).T
        
        simils = []
        for index, vector in enumerate(self.corpus_tfidf_dense):   
            simils.append((index, self.cosine_similarity(vector, query_vector[0])))

        ranked = sorted(simils, key=lambda x: x[1], reverse=True)
        return ranked

    def cosine_similarity(self, vector, q_vector):
        pass