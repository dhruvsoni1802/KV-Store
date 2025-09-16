from consistent_hash import ConsistentHash
from typing import Optional


class LoadBalancer:
    def __init__(self, servers: list):
        self.hash_ring = ConsistentHash(servers)
        self.stats_counter = 0
    
    def get_backend_url(self, path: str, server_param: str = None) -> str:
        key = self._extract_key_from_path(path)
        
        if key:
            # Use consistent hashing for key-based requests
            server = self.hash_ring.get_server(key)
            if server is None:
                raise Exception("No servers available in hash ring")
            return f"http://{server}"
        else:
            # For stats endpoints, server parameter is mandatory
            if path in ["cache/stats", "db/stats"]:
                if not self.hash_ring.servers:
                    raise Exception("No servers configured")
                
                if not server_param:
                    raise Exception(f"Server parameter is required for {path}. Available servers: {self.hash_ring.servers}")
                
                if server_param in self.hash_ring.servers:
                    return f"http://{server_param}"
                else:
                    raise Exception(f"Server '{server_param}' not found. Available servers: {self.hash_ring.servers}")
            else:
                # Fallback to first server for other non-key requests
                if not self.hash_ring.servers:
                    raise Exception("No servers configured")
                return f"http://{self.hash_ring.servers[0]}"
    
    def _extract_key_from_path(self, path: str) -> Optional[str]:
        if path.startswith("put/") or path.startswith("get/"):
            parts = path.split("/", 1)
            if len(parts) > 1:
                return parts[1]
        return None
