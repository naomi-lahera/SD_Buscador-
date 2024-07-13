from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from logic.build.preprocessing_data.preprocess import prepro
from gensim.similarities import MatrixSimilarity
from typing import List
from data_access_layer.controller_interface import BaseController
from logic.models.model_interface import ModelSearchInterface
class Retrieval_Vectorial(ModelSearchInterface):
    def __init__(self):
        pass
    def retrieve(self, query, controller: BaseController, no_docs: int = 1):
        id_tf_documents = controller.get_documents_for_query()

        # Crear un diccionario y corpus para el modelo TF-IDF
        dictionary = controller.dictionary
        corpus: List = [bow for _, bow in id_tf_documents]
        # Convertir las cadenas a listas de Python
        listas_convertidas = [[eval(item)] for item in corpus]

        # Aplanar la lista
        corpus = [item for sublist in listas_convertidas for item in sublist]

        model = TfidfModel(corpus)  # fit model

        # Tokenizar y convertir la consulta a BoW
        prep_query = prepro.tokenize_corpus([query])[0]
        query_bow, missings = dictionary.doc2bow(prep_query, return_missing=True)

        # Inicializa un contador para los términos faltantes
        missing_count = {}

        # Itera sobre el BoW para identificar y contar los términos faltantes
        for term_id, freq in missings.items():
            if term_id not in dictionary.token2id:
                missing_count[term_id] = freq

        # Agrega los términos faltantes al BoW con un recuento de 0
        for term_id, freq in missing_count.items():
            query_bow.append((term_id, freq))

        # Calcular el TF-IDF para la consulta en relación con cada documento
        query_tfidf = model[query_bow]

        # Crear un índice de similitud a partir del corpus TF-IDF
        index = MatrixSimilarity(model[corpus])

        # Calcular la similitud de la consulta con cada documento
        sims = index[query_tfidf]

        # Ordenar los documentos por similitud
        sorted_sims_indices = sims.argsort()[::-1][:no_docs]

        # Obtener los IDs de los documentos más relevantes
        most_relevant_doc_ids = [id_tf_documents[i][0] for i in sorted_sims_indices]
        documents = [controller.get_document_by_id(doc_id) for doc_id in most_relevant_doc_ids]

        return documents