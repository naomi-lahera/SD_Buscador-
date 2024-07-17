import sqlite3
import os
from joblib import load, dump
from gensim.corpora import Dictionary
from logic.build.preprocessing_data.preprocess import prepro
import json
from data_access_layer.controller_interface import BaseController

def read_or_create_joblib(ip):
    ip = str(ip)
    """
    Intenta leer un archivo .joblib. Si no existe, crea uno con el objeto_predeterminado.
    :param nombre_archivo: Nombre del archivo .joblib a leer o crear.
    :param objeto_predeterminado: Objeto a guardar si el archivo no existe.
    :return: Contenido del archivo .joblib o el objeto_predeterminado.
    """


    if not os.path.exists(f"src/server/data/nodes_data/{ip}/"):
        url = f"src/server/data/nodes_data/{ip}/"
        # print(f"Carpeta creada en: {url}")

        os.makedirs(f"src/server/data/nodes_data/{ip}/", exist_ok=True)


    if os.path.exists(f"src/server/data/nodes_data/{ip}/dictionary.joblib"):
        # El archivo existe, cargar y retornar su contenido
        # print("EL joblib ya existe")
        return load(f"src/server/data/nodes_data/{ip}/dictionary.joblib")
    else:
        # El archivo no existe, crear uno nuevo con el objeto predeterminado
        dump(Dictionary(), f"src/server/data/nodes_data/{ip}/dictionary.joblib")
        # print("EL joblib fue creado correctamente")
        return Dictionary()

class DocumentoController(BaseController):
    dictionary:Dictionary
    def __init__(self,ip):
        self.ip = ip
        DocumentoController.dictionary = read_or_create_joblib(ip)

    def connect(self):
        return sqlite3.connect(f"src/server/data/nodes_data/{self.ip}/database.db")

    def create_document(self, texto_documento, table=-1): #? Annadi la tabla a la que se va a annadir e documento
        tokens_documento = prepro.tokenize_corpus([texto_documento])
        DocumentoController.dictionary.add_documents(tokens_documento)
        tf = DocumentoController.dictionary.doc2bow(tokens_documento[0])

        # Convertir la lista tf a una cadena JSON
        tf_json = json.dumps(tf)

        # Conectar a la base de datos y verificar si la tabla existe
        conexion = self.connect()
        cursor = conexion.cursor()

        if table == -1:
            table = 'documentos'
        if table == 0:
            table = 'replica_pred'
        if table == 1:
            table = 'replica_succ'

        # Insertar los datos
        cursor.execute(f'''
            INSERT INTO {table} (texto_documento, tf) VALUES (?, ?)
        ''', (texto_documento, tf_json))
        conexion.commit()
        conexion.close()

        #TODO Hay que arreglar esto. Document Controller no tiene leader.
        #TODO Hay que hacer tambien que no guarde documentos que ya tiene
        # if self.leader:
        if True:
            dump(DocumentoController.dictionary, f"src/server/data/nodes_data/leader/dictionary.joblib")
        else:
            dump(DocumentoController.dictionary, f"src/server/data/nodes_data/{self.ip}/dictionary.joblib")

        # print("Diccionario actualizado y guardado.")

    def get_documents(self):
        conexion = self.connect()
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM documentos')
        documentos = cursor.fetchall()
        conexion.close()
        # id2tok = { x: y for y, x in DocumentoController.dictionary.token2id.items()}
        # print({ id2tok[k]:v for k,v in DocumentoController.dictionary.cfs.items()})

        return documentos

    def get_document_by_id(self, _id):
        conexion = self.connect()
        cursor = conexion.cursor()
        cursor.execute('SELECT texto_documento FROM documentos WHERE id = ?', (_id,))
        documento = cursor.fetchone()
        conexion.close()
        return documento

    def get_documents_for_query(self):
        conexion = self.connect()
        cursor = conexion.cursor()
        cursor.execute('SELECT id, tf FROM documentos')
        documentos = cursor.fetchall()
        conexion.close()
        return documentos

    def update_document(self, id, texto_documento=None):
        conexion = self.connect()
        cursor = conexion.cursor()

        if texto_documento is not None:
            cursor.execute('SELECT texto_documento FROM documentos WHERE id = ?', (id,))
            documento = cursor.fetchone()[0]

            tokens_documento = prepro.tokenize_corpus([documento])

            bow = DocumentoController.dictionary.doc2bow(tokens_documento[0])

            for word, count in bow:
                DocumentoController.dictionary.cfs[word] -= count
                DocumentoController.dictionary.dfs[word] -= 1
            cursor.execute('''
                UPDATE documentos SET texto_documento = ? WHERE id = ?
            ''', (texto_documento, id))

        tokens_texto_documento = prepro.tokenize_corpus([texto_documento])
        tf = DocumentoController.dictionary.doc2bow(tokens_texto_documento[0])
        tf_json = json.dumps(tf)


        if tf_json is not None:
            cursor.execute('''
                UPDATE documentos SET tf = ? WHERE id = ?
            ''', (tf_json, id))

        conexion.commit()
        conexion.close()

        DocumentoController.dictionary.add_documents(tokens_texto_documento)
        dump(DocumentoController.dictionary, 'dictionary.joblib')

        # print("Diccionario actualizado y guardado.")

    def delete_document(self, id):
        conexion = self.connect()
        cursor = conexion.cursor()
        cursor.execute('SELECT texto_documento FROM documentos WHERE id = ?', (id,))

        documento = cursor.fetchone()[0]
        tokens_documento = prepro.tokenize_corpus([documento])

        bow = DocumentoController.dictionary.doc2bow(tokens_documento[0])

        for word, count in bow:
            DocumentoController.dictionary.cfs[word] -= count
            DocumentoController.dictionary.dfs[word] -= 1

        cursor = conexion.cursor()
        cursor.execute('DELETE FROM documentos WHERE id = ?', (id,))
        conexion.commit()
        conexion.close()
        dump(DocumentoController.dictionary, 'dictionary.joblib')

        # print("Diccionario actualizado y guardado.")

    def delete_all_documents(self):
        conexion = self.connect()
        cursor = conexion.cursor()

        # Eliminar todos los documentos
        cursor.execute('DELETE FROM documentos')

        # Actualizar el diccionario después de eliminar los documentos
        DocumentoController.dictionary.clear()
        dump(DocumentoController.dictionary, 'dictionary.joblib')

        conexion.commit()
        conexion.close()

        # print("Todos los documentos eliminados y diccionario actualizado.")
        
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



