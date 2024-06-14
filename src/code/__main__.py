from build_data.builder_vectorial_model import init
from grocer.grocer_tfidf_joblib import grocer_vectorial_model_joblib

def run():
    init('./test_documents')
    query = 'Para especificar el nombre y el tag de la imagen que estás creando en un Dockerfile, no se puede hacer directamente en el cuerpo del Dockerfile. El Dockerfile se encarga de definir cómo se construye la imagen, pero el nombre y el tag de la imagen resultante se establecen durante el proceso de construcción y etiquetado de la imagen, no dentro del Dockerfile'
    print('query: ', query)
    for doc in grocer_vectorial_model_joblib.get_docs_query(query):
        print(doc.title)
    print()
        
    print('query: ', query)
    query = 'Dockerfile'
    for doc in grocer_vectorial_model_joblib.get_docs_query(query):
        print(doc.title)
    print()
        
    print('query: ', query)
    query = 'Se desenreda el pelo con peine de amrfil y aunque se hace tirones no llora ni hace asi.'
    for doc in grocer_vectorial_model_joblib.get_docs_query(query):
        print(doc.title)
    print()


if __name__ == '__main__':
    run()