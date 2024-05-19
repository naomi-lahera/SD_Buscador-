import os
import glob
# from PyPDF2 import PdfFileReader
# from docx import Document
from typing import List 

from gensim.models import TfidfModel
from gensim.matutils import corpus2dense
from gensim.corpora import Dictionary
from preprocessing_data.preprocess import prepro
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
        _, ext = os.path.splitext(file_path)
        if ext.lower() in ['.pdf', '.docx', '.txt', '.md']:
            print(f"Processing file: {file_path}")
            
            # if ext == ".pdf":
            #     text = read_pdf(file_path)
            # elif ext == ".docx":
            #     text = read_docx(file_path)
            # elif ext in ['.txt', '.md']:
            #     text = read_txt_md(file_path)
            
            text = read_txt_md(file_path)
            
            print(text[:100])  # Print the first part of the extracted text
            
            docs.append(text)
    
    return docs
    
def init(folder_path):
    docs_text = process_files_in_folder(folder_path)
    documents: List[document] = []
    tokenized_docs: dict[int, List[str]] = dict()

    for doc_text in docs_text:
        new_doc = document(None, doc_text)
        tokenized_docs[new_doc.id] = prepro.tokenize(doc_text)
        
        documents.append(new_doc)
        
    dictionary: Dictionary = prepro.get_dictionary(tokenized_docs.values())
    tfidf_object = TfidfModel(prepro.get_bow_corpus(tokenized_docs.values(), dictionary))
    
    for doc in documents:
        doc.doc_tfidf_dense = corpus2dense([tfidf_object[dictionary.doc2bow(tokenized_docs[doc.id])]], dictionary.num_pos, 1)
        
    save_file(tfidf_object, './../data/joblib', 'tfidf_object')
    save_file(dictionary, './../data/joblib', 'dictionary')
    save_file(documents, './../data/joblib', 'documents')
        
def load_corpus(self, corpus_name):
    try:
        corpus = load_file('./../data', corpus_name)
        print('loaded corpus...')
    except:
        dataset = ir_datasets.load("cranfield")
        corpus = dict()
        for doc in dataset.docs_iter():
            corpus[doc[0]] = doc[2]
        save_file(corpus, './../data', 'corpus')
        print('saved corpus...')
        
    return corpus

def process_corpus(corpus):
    tokenized_docs = prepro.tokenize_corpus(corpus)
    print('tokenized corpus...')
    dictionary = prepro.get_dictionary(tokenized_docs)
    print('builded dictionary...')
    corpus_bow = prepro.get_bow_corpus(tokenized_docs, dictionary)
    print('builded corpus to bow...')
    
    return tokenized_docs, dictionary, corpus_bow

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
init('./test_documents')