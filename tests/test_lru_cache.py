import pytest
from src.structures.linked_list import DoubleLinkedList, DoubleLinkedElement
from src.functools.lru_cache import LruCache, NotValidKeyError


# ---------------------------------------------------------------------------
# DoubleLinkedElement unit tests
# ---------------------------------------------------------------------------

class TestDoubleLinkedElement:

    def test_init(self):
        el = DoubleLinkedElement("k", "v")
        assert el.get_key() == "k"
        assert el.get_value() == "v"
        assert el.next() is None
        assert el.prev() is None

    def test_set_value(self):
        el = DoubleLinkedElement("k", "v")
        el.set_value("new")
        assert el.get_value() == "new"

    def test_set_next_and_prev(self):
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        a.set_next(b)
        b.set_prev(a)
        assert a.next() is b
        assert b.prev() is a


# ---------------------------------------------------------------------------
# LinkedList unit tests
# ---------------------------------------------------------------------------

class TestLinkedList:

    def test_empty_list(self):
        ll = DoubleLinkedList()
        assert len(ll) == 0
        assert ll.get_head() is None
        assert ll.get_tail() is None

    def test_add_single_element(self):
        ll = DoubleLinkedList()
        el = DoubleLinkedElement("k", 1)
        ll.add_element(el)
        assert len(ll) == 1
        assert ll.get_head() is el
        assert ll.get_tail() is el

    def test_add_multiple_elements(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        c = DoubleLinkedElement("c", 3)
        ll.add_element(a)
        ll.add_element(b)
        ll.add_element(c)
        assert len(ll) == 3
        assert ll.get_head() is c  # ← MRU
        assert ll.get_tail() is a  # ← LRU

    def test_remove_only_element(self):
        ll = DoubleLinkedList()
        el = DoubleLinkedElement("k", 1)
        ll.add_element(el)
        ll.remove_element(el)
        assert len(ll) == 0
        assert ll.get_head() is None
        assert ll.get_tail() is None

    def test_remove_head(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        ll.add_element(a)
        ll.add_element(b)
        ll.remove_element(a)
        assert ll.get_head() is b
        assert b.prev() is None

    def test_remove_tail(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        ll.add_element(a)
        ll.add_element(b)
        ll.remove_element(b)
        assert ll.get_tail() is a
        assert a.next() is None

    def test_remove_middle(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        c = DoubleLinkedElement("c", 3)
        ll.add_element(a)
        ll.add_element(b)
        ll.add_element(c)
        ll.remove_element(b)
        assert len(ll) == 2
        assert a.prev() is c
        assert c.next() is a

    def test_move_to_head_already_head(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        ll.add_element(a)
        ll.add_element(b)
        ll.move_to_head(a)
        assert ll.get_head() is a
        assert ll.get_tail() is b

    def test_move_to_head_from_tail(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        ll.add_element(a)
        ll.add_element(b)
        ll.move_to_head(b)
        assert ll.get_head() is b
        assert ll.get_tail() is a
        assert b.prev() is None
        assert a.next() is None

    def test_move_to_head_from_middle(self):
        ll = DoubleLinkedList()
        a = DoubleLinkedElement("a", 1)
        b = DoubleLinkedElement("b", 2)
        c = DoubleLinkedElement("c", 3)
        ll.add_element(a)
        ll.add_element(b)
        ll.add_element(c)
        ll.move_to_head(b)
        assert ll.get_head() is b
        assert b.next() is c
        assert a.prev() is c
        assert a.next() is None


# ---------------------------------------------------------------------------
# LruCache unit tests
# ---------------------------------------------------------------------------

class TestLruCache:

    def test_get_missing_key_returns_none(self):
        cache = LruCache(maxsize=3)
        assert cache.get("missing") is None

    def test_put_and_get(self):
        cache = LruCache(maxsize=3)
        cache.put("a", 1)
        assert cache.get("a") == 1

    def test_put_none_key_raises(self):
        cache = LruCache(maxsize=3)
        with pytest.raises(NotValidKeyError):
            cache.put(None, 1)

    def test_put_updates_existing_value(self):
        cache = LruCache(maxsize=3)
        cache.put("a", 1)
        cache.put("a", 99)
        assert cache.get("a") == 99

    def test_put_update_moves_to_head(self):
        cache = LruCache(maxsize=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("a", 99)
        assert cache._list.get_head().get_key() == "a"

    def test_evicts_lru_when_full(self):
        cache = LruCache(maxsize=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # "a" should be evicted
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_get_moves_to_head(self):
        cache = LruCache(maxsize=2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")       # access "a" → "b" is now LRU
        cache.put("c", 3)    # "b" should be evicted
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3

    def test_cache_size_does_not_exceed_maxsize(self):
        cache = LruCache(maxsize=3)
        for i in range(10):
            cache.put(f"k{i}", i)
        assert len(cache._list) == 3
        assert len(cache.cache) == 3

    def test_single_slot_cache(self):
        cache = LruCache(maxsize=1)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_put_does_not_duplicate_in_list(self):
        cache = LruCache(maxsize=3)
        cache.put("a", 1)
        cache.put("a", 2)
        cache.put("a", 3)
        assert len(cache._list) == 1

    def test_lru_order_after_multiple_operations(self):
        cache = LruCache(maxsize=3)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.get("a")        # order: a, c, b
        cache.put("d", 4)     # evicts "b"
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3
        assert cache.get("d") == 4
