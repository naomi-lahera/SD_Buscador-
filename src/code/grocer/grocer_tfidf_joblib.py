# import sys
# import os

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

import joblib
from grocer_interface import grocer
from build_data.preprocessing_data.preprocess import prepro
from models.vectorial_model import vectorial_model
from core.doc import document

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
    
    def get_doc_query(query):
        dictionary = grocer_vectorial_model_joblib.load_file('./../data/joblib', 'dictionary')
        tfidf_object = grocer_vectorial_model_joblib.load_file('./../data/joblib', 'tfidf_object')
        docs_ = grocer_vectorial_model_joblib.load_file('./../data/joblib', 'docs')
        docs = [document(doc) for doc in docs_]
            
        vectorial_model.retrieve_documents(tfidf_object, docs, dictionary, query)
    