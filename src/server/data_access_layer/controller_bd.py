import sqlite3
import os
from joblib import load, dump
from gensim.corpora import Dictionary
from logic.build.preprocessing_data.preprocess import prepro
import json
from data_access_layer.controller_interface import BaseController

def read_or_create_joblib(ip):
    ip = str(ip)
    directory_path = f"src/server/data/nodes_data/{ip}/"
    os.makedirs(directory_path, exist_ok=True)
    dictionary_path = os.path.join(directory_path, "dictionary.joblib")

    # Verificar si el archivo existe y, en caso afirmativo, eliminarlo
    if os.path.exists(dictionary_path):
        os.remove(dictionary_path)

    # Crear un nuevo diccionario y guardar el archivo
    new_dictionary = Dictionary()
    dump(new_dictionary, dictionary_path)

    return new_dictionary

class DocumentoController(BaseController):
    dictionary: Dictionary
    
    def __init__(self, ip):
        self.ip = ip
        DocumentoController.dictionary = read_or_create_joblib(ip)
        
    def connect(self):
        return sqlite3.connect(f"src/server/data/nodes_data/{self.ip}/database.db")

    def create_document(self, id, text, table):
        try:
            tokens = prepro.tokenize_corpus([text])
            DocumentoController.dictionary.add_documents(tokens)
            tf = DocumentoController.dictionary.doc2bow(tokens[0])

            tf_json = json.dumps(tf)

            conn = self.connect()
            cursor = conn.cursor()


            cursor.execute(f'''
                INSERT INTO {table} (id, text, tf) VALUES (?, ?, ?)
            ''', (id, text, tf_json))
            conn.commit()
            conn.close()

            dump(DocumentoController.dictionary, f"src/server/data/nodes_data/{self.ip}/dictionary.joblib")
        except:
            pass


    def get_documents(self, table):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table}')
        docs = cursor.fetchall()
        conn.close()
        
        return docs
    
    def get_document_by_id(self, _id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT text FROM documentos WHERE id = ?', (_id,))
        doc = cursor.fetchone()
        conn.close()
        
        return doc
    
    def get_documents_for_query(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT id, tf FROM documentos')
        doc = cursor.fetchall()
        conn.close()
        
        return doc

    def update_document(self, id, table, text=None):
        conn = self.connect()
        cursor = conn.cursor()
        
        if text is not None:
            cursor.execute(f'SELECT text FROM {table} WHERE id = ?', (id,))
            doc = cursor.fetchone()[0]
            
            tokens = prepro.tokenize_corpus([doc])
            
            bow = DocumentoController.dictionary.doc2bow(tokens[0])

            for word, count in bow:
                DocumentoController.dictionary.cfs[word] -= count
                DocumentoController.dictionary.dfs[word] -= 1
            cursor.execute(f'''
                UPDATE {table} SET text = ? WHERE id = ?
            ''', (text, id))
        
        tokens_text = prepro.tokenize_corpus([text])
        tf = DocumentoController.dictionary.doc2bow(tokens_text[0])
        tf_json = json.dumps(tf)
        
        
        if tf_json is not None:
            cursor.execute(f'''
                UPDATE {table} SET tf = ? WHERE id = ?
            ''', (tf_json, id))
            
        conn.commit()
        conn.close()
        
        DocumentoController.dictionary.add_documents(tokens_text)
        dump(DocumentoController.dictionary, 'dictionary.joblib')

    def delete_document(self, id, table):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'SELECT text FROM {table} WHERE id = ?', (id,))
        
        doc = cursor.fetchone()[0]
        tokens = prepro.tokenize_corpus([doc])
        
        bow = DocumentoController.dictionary.doc2bow(tokens[0])
        
        for word, count in bow:
            DocumentoController.dictionary.cfs[word] -= count
            DocumentoController.dictionary.dfs[word] -= 1
        
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table} WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        dump(DocumentoController.dictionary, 'dictionary.joblib')

    def delete_all_documents(self):
        conn = self.connect()
        cursor = conn.cursor()

        # Eliminar todos los documentos
        cursor.execute('DELETE FROM documentos')

        # Actualizar el diccionario después de eliminar los documentos
        DocumentoController.dictionary.clear()
        dump(DocumentoController.dictionary, 'dictionary.joblib')

        conn.commit()
        conn.close()

    def get_docs_between(self, tables, min, max):
        conn = self.connect()
        cursor = conn.cursor()

        table = tables[0]
        if table == -1:
            table = 'documentos'
        if table == 0:
            table = 'replica_pred'
        if table == 1:
            table = 'replica_succ'
        query = f'SELECT * FROM {table} WHERE id BETWEEN {min} AND {max}'

        for table in tables[:1]:
            if table == -1:
                table = 'documentos'
            if table == 0:
                table = 'replica_pred'
            if table == 1:
                table = 'replica_succ'
                
            query += f"""
                    UNION
                    SELECT * FROM {table} WHERE id BETWEEN {min} AND {max}
                    """
        
        cursor.execute(query)
        
        docs = cursor.fetchall()
        conn.close()
        
        return docs

    def create_doc_list(self, doc_list, table):
        for doc in doc_list:
            self.create_document(doc, table)

        # print("Diccionario actualizado y guardado.")



