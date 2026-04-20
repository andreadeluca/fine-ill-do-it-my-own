import pytest
import hashlib
from bisect import insort
from src.sys_design.hash_ring import Hasher, HashRing, INode, PhysicalNode, VirtualNode, HashException


class MD5Hasher(Hasher):
    def hash(self, string: str) -> str:
        return hashlib.md5(string.encode()).hexdigest()


class ConstantHasher(Hasher):
    """Restituisce sempre lo stesso hash — utile per testare collisioni e duplicati."""
    def hash(self, string: str) -> str:
        return "a" * 32


class SequentialHasher(Hasher):
    """Restituisce hash incrementali deterministici basati sull'input."""
    def __init__(self):
        self._map: dict[str, str] = {}
        self._counter = 0

    def hash(self, string: str) -> str:
        if string not in self._map:
            self._map[string] = format(self._counter * 1000, '032x')
            self._counter += 1
        return self._map[string]


class BrokenHasher(Hasher):
    """Lancia sempre eccezione."""
    def hash(self, string: str) -> str:
        raise HashException("Hasher rotto")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def hasher():
    return MD5Hasher()

@pytest.fixture
def ring(hasher):
    return HashRing(hasher)

@pytest.fixture
def node_a():
    return INode("NodeA")

@pytest.fixture
def node_b():
    return INode("NodeB")

@pytest.fixture
def node_c():
    return INode("NodeC")


# ---------------------------------------------------------------------------
# VirtualNode
# ---------------------------------------------------------------------------

class TestVirtualNode:

    def test_lt(self):
        pn = PhysicalNode("X")
        vn1 = VirtualNode(pn, 0, 10)
        vn2 = VirtualNode(pn, 1, 20)
        assert vn1 < vn2
        assert not vn2 < vn1

    def test_gt(self):
        pn = PhysicalNode("X")
        vn1 = VirtualNode(pn, 0, 10)
        vn2 = VirtualNode(pn, 1, 20)
        assert vn2 > vn1
        assert not vn1 > vn2

    def test_lt_wrong_type_raises(self):
        pn = PhysicalNode("X")
        vn = VirtualNode(pn, 0, 10)
        with pytest.raises(TypeError):
            _ = vn < "not a virtual node"

    def test_gt_wrong_type_raises(self):
        pn = PhysicalNode("X")
        vn = VirtualNode(pn, 0, 10)
        with pytest.raises(TypeError):
            _ = vn > 42

    def test_name_format(self):
        pn = PhysicalNode("db")
        vn = VirtualNode(pn, 3, 999)
        assert vn.name == "db_3"

    def test_physical_node_property(self):
        pn = PhysicalNode("db")
        vn = VirtualNode(pn, 0, 1)
        assert vn.physical_node is pn

    def test_hash_property(self):
        pn = PhysicalNode("db")
        vn = VirtualNode(pn, 0, 12345)
        assert vn.hash == 12345


# ---------------------------------------------------------------------------
# add_node
# ---------------------------------------------------------------------------

class TestAddNode:

    def test_add_single_node_creates_virtual_nodes(self, ring, node_a):
        ring.add_node(node_a, replicas=5)
        assert len(ring.virtual_nodes) == 5

    def test_add_single_node_default_replicas(self, ring, node_a):
        ring.add_node(node_a)
        assert len(ring.virtual_nodes) == 10

    def test_add_node_registers_physical_node(self, ring, node_a):
        ring.add_node(node_a)
        assert "NodeA" in ring.physical_nodes

    def test_virtual_nodes_are_sorted(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=20)
        ring.add_node(node_b, replicas=20)
        hashes = [vn.hash for vn in ring.virtual_nodes]
        assert hashes == sorted(hashes)

    def test_sorted_keys_match_virtual_nodes(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        expected = sorted(vn.hash for vn in ring.virtual_nodes)
        assert ring._sorted_key == expected

    def test_add_duplicate_node_is_idempotent(self, ring, node_a):
        ring.add_node(node_a, replicas=5)
        ring.add_node(node_a, replicas=5)
        assert len(ring.virtual_nodes) == 5
        assert list(ring.physical_nodes.keys()).count("NodeA") == 1

    def test_add_multiple_nodes_total_virtual_count(self, ring, node_a, node_b, node_c):
        ring.add_node(node_a, replicas=5)
        ring.add_node(node_b, replicas=5)
        ring.add_node(node_c, replicas=5)
        assert len(ring.virtual_nodes) == 15

    def test_add_node_broken_hasher_raises(self, node_a):
        ring = HashRing(BrokenHasher())
        with pytest.raises(HashException):
            ring.add_node(node_a)

    def test_all_virtual_nodes_point_to_correct_physical(self, ring, node_a):
        ring.add_node(node_a, replicas=10)
        for vn in ring.virtual_nodes:
            assert vn.physical_node.name == "NodeA"


# ---------------------------------------------------------------------------
# delete_node
# ---------------------------------------------------------------------------

class TestDeleteNode:

    def test_delete_removes_virtual_nodes(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=5)
        ring.add_node(node_b, replicas=5)
        ring.delete_node(node_a)
        assert len(ring.virtual_nodes) == 5
        for vn in ring.virtual_nodes:
            assert vn.physical_node.name == "NodeB"

    def test_delete_removes_physical_node(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=5)
        ring.add_node(node_b, replicas=5)
        ring.delete_node(node_a)
        assert "NodeA" not in ring.physical_nodes
        assert "NodeB" in ring.physical_nodes

    def test_delete_keeps_sorted_keys_sorted(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        ring.delete_node(node_a)
        assert ring._sorted_key == sorted(ring._sorted_key)

    def test_delete_sorted_keys_match_virtual_nodes(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        ring.delete_node(node_a)
        expected = sorted(vn.hash for vn in ring.virtual_nodes)
        assert ring._sorted_key == expected

    def test_delete_nonexistent_node_raises(self, ring, node_a):
        with pytest.raises(KeyError):
            ring.delete_node(node_a)

    def test_delete_all_nodes_empties_ring(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=5)
        ring.add_node(node_b, replicas=5)
        ring.delete_node(node_a)
        ring.delete_node(node_b)
        assert len(ring.virtual_nodes) == 0
        assert len(ring._sorted_key) == 0
        assert len(ring.physical_nodes) == 0


# ---------------------------------------------------------------------------
# get_node
# ---------------------------------------------------------------------------

class TestGetNode:

    def test_get_node_returns_physical_node(self, ring, node_a):
        ring.add_node(node_a, replicas=10)
        result = ring.get_node("request-123")
        assert isinstance(result, PhysicalNode)

    def test_get_node_single_node_always_returns_it(self, ring, node_a):
        ring.add_node(node_a, replicas=10)
        for i in range(50):
            result = ring.get_node(f"request-{i}")
            assert result.name == "NodeA"

    def test_get_node_is_deterministic(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        first = ring.get_node("req-xyz").name
        second = ring.get_node("req-xyz").name
        assert first == second

    def test_get_node_distributes_across_nodes(self, ring, node_a, node_b, node_c):
        ring.add_node(node_a, replicas=100)
        ring.add_node(node_b, replicas=100)
        ring.add_node(node_c, replicas=100)
        results = {ring.get_node(f"req-{i}").name for i in range(300)}
        assert results == {"NodeA", "NodeB", "NodeC"}

    def test_get_node_wraps_around_ring(self, ring):
        """Request con hash molto alto deve wrapparsi al primo nodo."""
        hasher = SequentialHasher()
        ring = HashRing(hasher)
        node = INode("Wrap")
        ring.add_node(node, replicas=5)
        result = ring.get_node("qualsiasi")
        assert result.name == "Wrap"

    def test_get_node_after_delete_never_returns_deleted(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=50)
        ring.add_node(node_b, replicas=50)
        ring.delete_node(node_a)
        for i in range(100):
            result = ring.get_node(f"req-{i}")
            assert result.name == "NodeB"

    def test_get_node_consistent_before_after_add(self, ring, node_a, node_b, node_c):
        """Un subset di richieste deve restare sullo stesso nodo dopo aggiunta."""
        ring.add_node(node_a, replicas=50)
        ring.add_node(node_b, replicas=50)

        mapping_before = {f"req-{i}": ring.get_node(f"req-{i}").name for i in range(200)}

        ring.add_node(node_c, replicas=50)

        moved = 0
        for key, old_node in mapping_before.items():
            new_node = ring.get_node(key).name
            if new_node != old_node:
                moved += 1

        # Con consistent hashing, solo ~1/3 delle chiavi dovrebbe spostarsi
        assert moved < len(mapping_before) * 0.5


# ---------------------------------------------------------------------------
# Proprietà strutturali
# ---------------------------------------------------------------------------

class TestStructuralInvariants:

    def test_sorted_keys_always_sorted_after_operations(self, ring, node_a, node_b, node_c):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        ring.add_node(node_c, replicas=10)
        ring.delete_node(node_b)
        assert ring._sorted_key == sorted(ring._sorted_key)

    def test_sorted_keys_and_virtual_nodes_same_length(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=10)
        ring.add_node(node_b, replicas=10)
        assert len(ring._sorted_key) == len(ring.virtual_nodes)
        ring.delete_node(node_a)
        assert len(ring._sorted_key) == len(ring.virtual_nodes)

    def test_no_duplicate_hashes_in_sorted_keys(self, ring, node_a, node_b):
        ring.add_node(node_a, replicas=20)
        ring.add_node(node_b, replicas=20)
        assert len(ring._sorted_key) == len(set(ring._sorted_key))