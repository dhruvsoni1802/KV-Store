import hashlib
import bisect
from typing import List, Optional


class ConsistentHash:
    def __init__(self, servers: List[str], virtual_nodes: int = 150):
        self.servers = servers
        self.virtual_nodes = virtual_nodes
        self.ring = {}  # hash_value -> server
        self.sorted_keys = []  # sorted list of hash values
        
        # Add all servers to the ring
        for server in servers:
            self.add_server(server)
    
    def _hash(self, key: str) -> int:
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)
    
    def add_server(self, server: str):
        for i in range(self.virtual_nodes):
            virtual_key = f"{server}#{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = server
            bisect.insort(self.sorted_keys, hash_value)
    
    def remove_server(self, server: str):
        keys_to_remove = []
        for hash_value, mapped_server in self.ring.items():
            if mapped_server == server:
                keys_to_remove.append(hash_value)
        
        for hash_value in keys_to_remove:
            del self.ring[hash_value]
            self.sorted_keys.remove(hash_value)
    
    def get_server(self, key: str) -> Optional[str]:
        if not self.sorted_keys:
            return None
        
        key_hash = self._hash(key)
        
        # Find the first server with hash >= key_hash
        index = bisect.bisect_left(self.sorted_keys, key_hash)
        
        # If we're at the end, wrap around to the first server
        if index == len(self.sorted_keys):
            index = 0
        
        hash_value = self.sorted_keys[index]
        return self.ring[hash_value]
