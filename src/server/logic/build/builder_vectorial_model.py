import os
import glob
# from PyPDF2 import PdfFileReader
# from docx import Document
from sklearn.decomposition import PCA


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
        if ext.lower() in ['.pdf', '.docx', '.txt', '.md']:
            print(f"Processing file: {file_path}")
            
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
    
def get_PCA(corpus_tfidf_dense):
    # Entrenando el modelo de reducción de dimensiones

    # Índice de varianza
    variance = 0.90
    reduction_model = PCA(variance).fit(corpus_tfidf_dense)

    return reduction_model
