from grocer_tfidf_joblib import grocer_vectorial_model_joblib

for doc in grocer_vectorial_model_joblib.get_doc_query('test'):
    print(doc.text)