import joblib

def save_file(file, path, file_name):
    # joblib.dump(file, f'{path}/{file_name}.joblib')
    joblib.dump(file, f'{file_name}.joblib')
    
def load_file(path, file_name):
    tfidf_matrix = joblib.load(file_name)
    return tfidf_matrix