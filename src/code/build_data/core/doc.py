import uuid

class document:
    def __init__(self, title, text, id=None):
        self.id = id if id else self.generate_id()
        self.content = doc_content(title, text)
        self.doc_tfidf_dense = None

    @staticmethod
    def generate_id():
        return uuid.uuid4()
    
class doc_content:
    def __init__(self, title, text):
        self.text = text
        self.title = title