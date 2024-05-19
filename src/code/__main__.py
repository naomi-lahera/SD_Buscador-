from build_data.builder_vectorial_model import init
from grocer.grocer_tfidf_joblib import grocer_vectorial_model_joblib

def run():
    init('./test_documents')
    for doc in grocer_vectorial_model_joblib.get_docs_query('test'):
        print(doc.text)

if __name__ == '__main__':
    run()