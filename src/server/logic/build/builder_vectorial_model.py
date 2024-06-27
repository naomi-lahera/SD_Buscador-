import os
import glob
# from PyPDF2 import PdfFileReader
# from docx import Document
from typing import List 

from gensim.models import TfidfModel
from sklearn.decomposition import PCA
from gensim.matutils import corpus2dense
from gensim.corpora import Dictionary
from logic.build.preprocessing_data.preprocess import prepro
from core.doc import document
import joblib
import ir_datasets

# def read_pdf(file_path):
#     with open(file_path, "rb") as file:
#         pdf = PdfFileReader(file)
#         text = ""
#         for page_num in range(pdf.getNumPages()):
#             text += pdf.getPage(page_num).extractText()
#     return text

# def read_docx(file_path):
#     doc = Document(file_path)
#     text = "\n".join([para.text for para in doc.paragraphs])
#     return text

def read_txt_md(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def process_files_in_folder(folder_path):
    docs = []
    for file_path in glob.glob(os.path.join(folder_path, "*")):
        name, ext = os.path.splitext(file_path)
        # print('file_name: ', name)
        if ext.lower() in ['.pdf', '.docx', '.txt', '.md']:
            # print(f"Processing file: {file_path}")
            
            # if ext == ".pdf":
            #     text = read_pdf(file_path)
            # elif ext == ".docx":
            #     text = read_docx(file_path)
            # elif ext in ['.txt', '.md']:
            #     text = read_txt_md(file_path)
            
            text = read_txt_md(file_path)
            
            # print(text[:100])  # Print the first part of the extracted text
            
            docs.append((name, text))
    
    return docs
    
def init(folder_path):
    #TODO Poner el titulo del documento que sea el nombre del archivo que se esta leyendo
    docs_text = process_files_in_folder(folder_path)
    documents: dict[int, document] = dict()
    tokenized_docs: dict[int, List[str]] = dict()

    for title, doc_text in docs_text:
        new_doc = document(title, doc_text)
        tokenized_docs[new_doc.id] = prepro.tokenize(doc_text)
        
        documents[new_doc.id] = new_doc
        
    dictionary: Dictionary = prepro.get_dictionary(tokenized_docs.values())
    tfidf_object = TfidfModel(prepro.get_bow_corpus(tokenized_docs.values(), dictionary))
    
    corpus2bow = [dictionary.doc2bow(doc) for doc in tokenized_docs.values()]
    
    corpus_tfidf_dense = corpus2dense(tfidf_object[corpus2bow], dictionary.num_pos, len(tokenized_docs)).T
    print('corpus_tfidf_dense: ' ,corpus_tfidf_dense)
    
    reduction_model = get_PCA(corpus_tfidf_dense)
    
    for doc in documents.values():
        doc2bow = dictionary.doc2bow(tokenized_docs[doc.id])
        dense_doc = corpus2dense([tfidf_object[doc2bow]], dictionary.num_pos, 1).T
        doc.doc_tfidf_dense = reduction_model.transform(dense_doc)[0]
        print('doc.doc_tfidf_dense: ' ,doc.doc_tfidf_dense)
        
    save_file(tfidf_object, './data/joblib', 'tfidf_object')
    save_file(reduction_model, './data/joblib', 'reduction_model')
    save_file(documents, './data/joblib', 'documents')
    save_file(dictionary, './data/joblib', 'dictionary')
    

# def load_corpus_cranfield(self, corpus_name):
#     dataset = ir_datasets.load("cranfield")
        
#     documents: List[document] = []
#     tokenized_docs: dict[int, List[str]] = dict()

#     for doc in dataset.docs_iter():
#         new_doc = document(doc[0], doc[2])
#         tokenized_docs[new_doc.id] = prepro.tokenize(doc[2])
        
#         documents.append(new_doc)
        
#     dictionary: Dictionary = prepro.get_dictionary(tokenized_docs.values())
#     tfidf_object = TfidfModel(prepro.get_bow_corpus(tokenized_docs.values(), dictionary))
    
#     for doc in documents:
#         doc.doc_tfidf_dense = corpus2dense([tfidf_object[dictionary.doc2bow(tokenized_docs[doc.id])]], dictionary.num_pos, 1)
    
#     save_file(tfidf_object, './data/joblib', 'tfidf_object_cranfirld')
#     save_file(dictionary, './data/joblib', 'dictionary_cranfirld')
#     save_file(documents, './data/joblib', 'documents_cranfirld')
#     print('saved corpus...')
    
def get_PCA(corpus_tfidf_dense):
    # Entrenando el modelo de reducción de dimensiones

    # Índice de varianza
    variance = 0.90
    reduction_model = PCA(variance).fit(corpus_tfidf_dense)

    return reduction_model

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
        
# process_files_in_folder('./test_documents')
# init('./test_documents')