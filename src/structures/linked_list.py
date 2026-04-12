from __future__ import annotations

from functools import lru_cache

from typing import Any

from src.structures.interfaces.ListInterface import ListInterface


class LinkedList(ListInterface):

    __slots__ = ['_head', '_tail', '_count']

    def __init__(self):
        self._head : DoubleLinkedElement | None = None
        self._tail : DoubleLinkedElement | None = None
        self._count : int = 0

    def add_element(self, obj: DoubleLinkedElement):
        if self._head is None: #Presuming that if the list has no head is a new list
            self._head = self._tail = obj
        else:
            self._tail.set_next(obj)
            obj.set_prev(self._tail)
            self._tail = obj
        self._count += 1

    def remove_element(self, obj : DoubleLinkedElement):
        if self._head == self._tail:
            self._head = self._tail = None
        elif obj == self._head:
            self._head = obj.next()
            self._head._prev = None
        elif obj == self._tail:
            self._tail = obj.prev()
            self._tail._next = None
        else:
            obj.prev().set_next(obj.next())
            obj.next().set_prev(obj.prev())
            del obj
        self._count -= 1

    def move_to_head(self, obj : DoubleLinkedElement):

        if obj == self._head:
            return
        elif obj == self._tail:
            self._tail = obj.prev()

        obj.prev().set_next(obj.next())
        if obj.next(): #if i'm not tail
            obj.next().set_prev(obj.prev())
        self._head.set_prev(obj)
        obj._next = self._head
        self._head = obj
        obj._prev = None

    def get_head(self) -> DoubleLinkedElement:
        return self._head

    def get_tail(self) -> DoubleLinkedElement:
        return self._tail

    def __len__(self) -> int:
        return self._count



class DoubleLinkedElement:

    __slots__ = ['_value', '_next', '_prev', '_key']

    def __init__(self, key = None,  value = None):
        self._next = None
        self._prev = None
        self._value = value
        self._key = key

    def get_value(self):
        return self._value

    def set_next(self, el : DoubleLinkedElement):
        self._next = el

    def set_prev(self, el : DoubleLinkedElement):
        self._prev = el

    def get_next(self) -> DoubleLinkedElement:
        return self._next

    def get_prev(self) -> DoubleLinkedElement:
        return self._prev

    def set_key(self, key : int):
        self._key = key

    def get_key(self) -> int:
        return self._key

    def set_value(self, value : int):
        self._value = value

    def next(self) -> DoubleLinkedElement:
        return self._next

    def prev(self) -> DoubleLinkedElement:
        return self._prev




