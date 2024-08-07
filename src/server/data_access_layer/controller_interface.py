from abc import ABC, abstractmethod
class BaseController(ABC):
    """
    Clase base abstracta que define la interfaz para todos los controladores.
    """
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def create_document(self, texto_documento, table):
        pass
    
    @abstractmethod
    def create_doc_list(self, doc_list, table):
        pass

    @abstractmethod
    def get_documents(self):
        pass

    @abstractmethod
    def get_document_by_id(self, _id):
        pass

    @abstractmethod
    def get_documents_for_query(self):
        pass

    @abstractmethod
    def update_document(self, id, texto_documento=None):
        pass

    @abstractmethod
    def delete_document(self, id):
        pass
    
    @abstractmethod
    def get_docs_between(self, tables, min, max):
        pass


