import spacy 
import nltk

nlp = spacy.load("en_core_web_sm")

def tokenize(corpus):
    tokenized_corpus = []
    stopwords = spacy.lang.en.stop_words.STOP_WORDS
    
    for doc_text in corpus:
        tokenized_doc = []
        for token in nlp(doc_text):
            if token.text.isalpha() and token.text not in stopwords:
                tokenized_doc.append(token.lemma_)
        tokenized_corpus.append(tokenized_doc)
    
    return tokenized_corpus
        