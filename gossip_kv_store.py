# gossip_kv_store.py
import socket
import threading
import json
import time
import random
from datetime import datetime

class GossipNode:
    def __init__(self, node_id, port, peers):
        self.node_id = node_id
        self.port = port
        self.peers = peers  # List of (ip, port)
        self.store = {}     # {key: (value, timestamp)}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(('0.0.0.0', port))
        print(f"[NODE {node_id}] Listening on port {port}")

    def put(self, key, value):
        timestamp = time.time()
        self.store[key] = (value, timestamp)
        print(f"[NODE {node_id}] PUT {key} = {value}")
        self._gossip_update(key, value, timestamp)

    def get(self, key):
        if key in self.store:
            value, ts = self.store[key]
            print(f"[NODE {node_id}] GET {key} = {value} (ts: {ts:.2f})")
            return value
        print(f"[NODE {node_id}] GET {key} = NOT FOUND")
        return None

    def _gossip_update(self, key, value, timestamp):
        message = {
            'type': 'update',
            'key': key,
            'value': value,
            'timestamp': timestamp,
            'origin': self.node_id
        }
        payload = json.dumps(message).encode()
        # Gossip to 2 random peers
        targets = random.sample(self.peers, min(2, len(self.peers)))
        for ip, port in targets:
            try:
                self.sock.sendto(payload, (ip, port))
            except:
                pass

    def _handle_message(self, data, addr):
        try:
            msg = json.loads(data.decode())
            if msg['type'] == 'update':
                key = msg['key']
                value = msg['value']
                ts = msg['timestamp']
                if key not in self.store or self.store[key][1] < ts:
                    self.store[key] = (value, ts)
                    print(f"[NODE {node_id}] GOSSIP UPDATE {key} = {value} from {msg['origin']}")
                    # Re-gossip with 50% probability
                    if random.random() < 0.5:
                        threading.Thread(target=self._gossip_update, args=(key, value, ts)).start()
        except:
            pass

    def start(self):
        def receiver():
            while True:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    self._handle_message(data, addr)
                except:
                    continue
        threading.Thread(target=receiver, daemon=True).start()

        # Periodic anti-entropy (full sync)
        def anti_entropy():
            while True:
                time.sleep(10)
                if self.peers:
                    target_ip, target_port = random.choice(self.peers)
                    sync_msg = {
                        'type': 'sync',
                        'store': self.store,
                        'node_id': self.node_id
                    }
                    try:
                        self.sock.sendto(json.dumps(sync_msg).encode(), (target_ip, target_port))
                    except:
                        pass
        threading.Thread(target=anti_entropy, daemon=True).start()

# === DEMO ===
if __name__ == "__main__":
    # Simulate 3 nodes
    nodes = [
        GossipNode("A", 5001, [("255.255.255.255", 5002), ("255.255.255.255", 5003)]),
        GossipNode("B", 5002, [("255.255.255.255", 5001), ("255.255.255.255", 5003)]),
        GossipNode("C", 5003, [("255.255.255.255", 5001), ("255.255.255.255", 5002)])
    ]
    for node in nodes:
        node.start()

    time.sleep(2)
    nodes[0].put("temperature", 25.5)
    time.sleep(3)
    nodes[1].get("temperature")
    nodes[2].get("temperature")