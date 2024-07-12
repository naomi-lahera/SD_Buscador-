from abc import ABC, abstractmethod
from data_access_layer.controller_interface import BaseController
class ModelSearchInterface(ABC):
    """
    Interfaz para clases que realizan búsquedas basadas en modelos.
    """
    @abstractmethod
    def retrieve(self, query: str, controller: BaseController):
        pass