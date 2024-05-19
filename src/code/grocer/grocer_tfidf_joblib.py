# import sys
# import os

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

import joblib
from grocer.grocer_interface import grocer
from models.vectorial_model import vectorial_model
# from vectorial_model import vectorial_model

class grocer_vectorial_model_joblib(grocer):
    def save_file(file, path, file_name):
        try:
            joblib.dump(file, f'{path}/{file_name}.joblib')
        except Exception as e:
            raise e

    def load_file(path, file_name):
        try:
            return joblib.load(f'{path}/{file_name}.joblib')
        except Exception as e:
            raise e

    def add_doc(doc_text):
        pass
        # path = './../data/joblib'
        # file_name = 'corpus'
        
        # try:
        #     return joblib.load(f'{path}/{file_name}.joblib')
        # except Exception as e:
        #     tokenized_text = prepro.tokenize(doc_text)
            
        #     joblib.dump(file, f'{path}/{file_name}.joblib')
    
    def update_doc():
        pass
    
    def delete_doc():
        pass

    def get_all_docs():
        pass
    
    def get_doc_id():
        pass
    
    def get_docs_query(query):
        dictionary = grocer_vectorial_model_joblib.load_file('./data/joblib', 'dictionary')
        print(f'dictionary : {type(dictionary)}')
        tfidf_object = grocer_vectorial_model_joblib.load_file('./data/joblib', 'tfidf_object')
        print('tfidf_object : ', type(tfidf_object))
        docs_ = grocer_vectorial_model_joblib.load_file('./data/joblib', 'documents')
        #docs = [document(doc) for doc in docs_]
            
        return vectorial_model.retrieve_documents(tfidf_object, docs_, dictionary, query)