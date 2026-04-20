from abc import ABC
from bisect import bisect_right, insort


class Hasher(ABC):
    def hash(self, string : str) -> str: ...

class HashException(Exception):
    def __init__(self, message : str):
        self.message = message

class INode:
    def __init__(self, name : str):
        self._name = name

    @property
    def name(self):
        return self._name

class PhysicalNode(INode):
    def __init__(self, name : str):
        super().__init__(name)

class VirtualNode(INode):

    __slots__ =["_hash", "_replica_no", "_physical_node"]

    def __init__(self, physical_node : PhysicalNode, replica_no : int, vn_hash : int):
        super().__init__(physical_node.name+"_"+str(replica_no))
        self._hash : int = vn_hash
        self._replica_no = replica_no
        self._physical_node : PhysicalNode = physical_node

    def __lt__(self, other):
            if isinstance(other, VirtualNode):
                return self._hash < other._hash
            else:
                raise TypeError(f"Incorrect type for matching in {self.__class__.__name__}")
    def __gt__(self, other):
        if isinstance(other, VirtualNode):
            return self._hash > other._hash
        else:
            raise TypeError(f"Incorrect type for matching in {self.__class__.__name__}")

    @property
    def physical_node(self):
        return self._physical_node

    @property
    def hash(self):
        return self._hash

    def __repr__(self) -> str:
        if self.__slots__ is not None:
            slots = []
            for cls in type(self).mro():
                slots.extend(getattr(cls, "__slots__", []))
            return format(slots, "#010x")
        else:
            return str(self.__dict__)



class HashRing:

    def __init__(self, hasher : Hasher):
        self.virtual_nodes : list[VirtualNode] = []
        self.physical_nodes : dict[str, PhysicalNode] = {}
        self._sorted_key : list[int] = []
        self._hasher = hasher

    def add_node(self, node: INode, replicas: int = 10):
        if node.name in self.physical_nodes:
            return

        physical_node = PhysicalNode(node.name)
        try:
            new_virtuals = [
                VirtualNode(
                    physical_node,
                    i,
                    int(self._hasher.hash(f"{physical_node.name}_{i}"), 16)
                )
                for i in range(replicas)
            ]
        except HashException as e:
            raise HashException(f"Hashing failed for {physical_node.name}: {e}")

        self.physical_nodes[physical_node.name] = physical_node
        for vn in new_virtuals:
            insort(self._sorted_key, int(vn.hash))
            insort(self.virtual_nodes, vn)


    def delete_node(self, node : INode):

        self.virtual_nodes = [
            vn for vn in self.virtual_nodes
            if vn.physical_node.name != node.name
        ]

        self._sorted_key = [vn.hash for vn in self.virtual_nodes]
        self._sorted_key.sort()

        del self.physical_nodes[node.name]

    def get_node(self, request_id : str):
        hashed_req = self._hasher.hash(f"{request_id}")
        return self.virtual_nodes[bisect_right(self._sorted_key, int(hashed_req, 16)) % len(self._sorted_key)].physical_node