from typing import Callable, Any
from threading import Lock, RLock

from ..structures.linkedlist import LinkedList, DoubleLinkedElement


class LruCache:

    def __init__(self, maxsize = 128):
        self.cache = {} #Dict that maps key -> DoubleLinkedElement
        self.maxsize = maxsize
        self._list = LinkedList()
        self.full : Callable = lambda:  len(self._list) >= maxsize
        self._lock = RLock()

    def put(self, key, value : Any):
        with self._lock:
            found_item = self.cache.get(key)
            if found_item:
                self._list.move_to_head(found_item)
                if found_item is not value:
                    self.cache[key] = value
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
            if found_item is not None:
                self._list.move_to_head(found_item)
                return self.cache[key].get_value()
            else:
                return None





