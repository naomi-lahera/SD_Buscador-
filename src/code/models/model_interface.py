from abc import ABC, abstractmethod

class model_interface:
    @staticmethod
    @abstractmethod
    def retrieve_documents():
        pass