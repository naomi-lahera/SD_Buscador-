from typing import List, Tuple

import spacy
nlp = spacy.load("en_core_web_sm")

# Facilita el trabajo con los términos indexados del corpus
from gensim.corpora import Dictionary

class prepro:
    @staticmethod
    def tokenize(text):
        """
        Tokenize and select text tokens
    
        Args:
        - text : str
            Document.
    
        Return:
        - list<str>
    
        """
    
        doc = nlp(text)
        tokens = []
        for token in doc:
            if token.text.isalpha(): 
                tokens.append(token.lemma_)
    
        return tokens
    
    @staticmethod
    def tokenize_corpus(corpus: List[str]) -> List[List[str]]:
        return [prepro.tokenize(doc) for doc in corpus]
    
    @staticmethod
    def get_dictionary(corpus : List[List[str]]) -> Dictionary:
        return Dictionary(corpus)
    
    @staticmethod
    def get_bow_corpus(corpus : List[List[str]], dictionary : Dictionary) -> List[List[Tuple[int, int]]]:
        return [dictionary.doc2bow(doc) for doc in corpus]
    
