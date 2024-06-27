from build_data.builder import Searcher
import joblib

def save_file(file, path, file_name):
        try:
            joblib.dump(file, f'{path}/{file_name}.joblib')
        except Exception as e:
            raise e

def run():
    toy_corpus = {
        0: 'Singular Value Decomposition',
        1: 'Probabilistic Latante Semantic Indexing',
        2: 'Latente Dirichlet Allocation',
        3: 'Sentence Latente Dirrichlet Allocation'
    }

    save_file(toy_corpus, './../data', 'toy_text_docs')
    print('saved file...')

    # sr = Searcher('toy_corpus')
    print(sr.corpus)

if __name__ == '__main__':
    run()