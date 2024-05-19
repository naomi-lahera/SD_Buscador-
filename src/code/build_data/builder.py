from models.gensim_models import vectorial_model
from preprocessing_data.preprocess import prepro
from middlware.grocer_interface import grocer
from info.save_info import save_file, load_file
import ir_datasets

class Builder():
    def __init__(self, corpus_name='corpus'):
        self.corpus: dict = self.init_corpus(corpus_name)
        print('initalized corpus...')
        
        self.prepro = prepro()
        self.tokenized_docs, self.dictionary, self.corpus_bow = self.process_corpus()
        print('processed corpus...')
        
        self.models = vectorial_model(self.corpus_bow, self.tokenized_docs, self.dictionary)
        
    def init_corpus(self, corpus_name):
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
            
    def load_corpus(self):
        corpus = load_file('./../data', 'corpus')
        print('loaded corpus...')
        
        return corpus
    
    def process_corpus(self):
        tokenized_docs = self.prepro.tokenize_corpus(self.corpus.values())
        print('tokenized corpus...')
        dictionary = self.prepro.get_dictionary(tokenized_docs)
        print('builded dictionary...')
        corpus_bow = self.prepro.get_bow_corpus(tokenized_docs, dictionary)
        print('builded corpus to bow...')
        
        return tokenized_docs, dictionary, corpus_bow

        