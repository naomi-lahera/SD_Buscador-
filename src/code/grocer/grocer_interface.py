from abc import ABC, abstractmethod

class grocer(ABC):
    @staticmethod
    @abstractmethod
    def add_doc():
        pass
    
    @staticmethod
    @abstractmethod
    def update_doc():
        pass
    
    @staticmethod
    @abstractmethod
    def delete_doc():
        pass
    
    @staticmethod
    @abstractmethod
    def get_all_docs():
        pass
    
    @staticmethod
    @abstractmethod
    def get_doc_id():
        pass
    
    @staticmethod
    @abstractmethod
    def get_doc_query():
        pass
    
    
    
    
    
