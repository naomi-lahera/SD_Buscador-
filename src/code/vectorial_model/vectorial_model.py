from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from save_info import save_file, load_file
from prepro_and_tokineze import tokenize

tf_idf_matrix = None
tf_idf_vect = None

def calculate_tf_idf(corpus, save=False):
    # Convertir cada lista de tokens en una cadena única
    preprocessed_docs = [' '.join(doc) for doc in corpus]
    
    # Crear el vectorizador y calcular la matriz TF-IDF
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(preprocessed_docs)
    
    if save:
        save_file(tfidf_vectorizer, './data/', 'tf_idf_vect')
        save_file(tfidf_matrix, './data/', 'tf_idf_matrix')
    
    return tfidf_matrix

def get_ordered_docs(query):
    global tf_idf_matrix
    global tf_idf_vect 
    
    if tf_idf_matrix or tf_idf_vect:
        tf_idf_vect = load_file('./data/', 'tf_idf_vect')
        tf_idf_matrix = load_file('./data/', 'tf_idf_matrix')
        
    query_tokens = tokenize([query])
    q_vector = tf_idf_vect.transform(query_tokens)
    
    # Calcular las similitudes del coseno entre la consulta y los documentos
    scores = cosine_similarity(q_vector, tf_idf_matrix)[0]

    scores = {i: score for i, score in enumerate(scores)}
    ordered_dict = dict(sorted(scores.items(), key=lambda item: item[1],nreverse = True))
    
    return ordered_dict.items()[:10]


calculate_tf_idf(load_file('./corpus/', 'tokenized_corpus.joblib')[:5], True)
get_ordered_docs('El patio de mi casa es particular')