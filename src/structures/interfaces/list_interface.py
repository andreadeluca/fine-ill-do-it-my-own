from abc import ABC


class ListInterface(ABC):

    def add_element(self, *args, **kwargs):
        pass

    def remove_element(self, *args, **kwargs):
        pass