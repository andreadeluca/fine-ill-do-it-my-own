from typing import Callable, Any
from threading import Lock, RLock

from src.structures.linked_list import DoubleLinkedList, DoubleLinkedElement

class NotValidKeyError(KeyError):
    pass

class LruCache:

    def __init__(self, maxsize = 128):
        self.cache = {} #Dict that maps key -> DoubleLinkedElement
        self.maxsize = maxsize
        self._list = DoubleLinkedList()
        self.full : Callable = lambda:  len(self._list) >= maxsize #O(1)
        self._lock = RLock()

    def put(self, key, value : Any):

        if key is None:
            raise NotValidKeyError

        with self._lock:
            found_item : DoubleLinkedElement = self.cache.get(key)
            if found_item:
                self._list.move_to_head(found_item)
                if found_item.get_value() != value:
                    found_item.set_value(value) #Dictionary update unnecessary. It already holds the correct object pointer.
            else:
                if self.full():
                    tail = self._list.get_tail()
                    del self.cache[tail.get_key()]
                    self._list.remove_element(tail)
                new_obj = DoubleLinkedElement(key,value)
                self.cache[key] = new_obj
                self._list.add_element(new_obj)

    def get(self, key : Any) -> Any:
        with self._lock:
            found_item = self.cache.get(key)
            if found_item is not None: #hit block
                self._list.move_to_head(found_item)
                return found_item.get_value()
            else: #miss block
                return None





