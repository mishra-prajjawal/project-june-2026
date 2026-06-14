import queue
import json
import threading

class SSEManager:
    """
    Thread-safe SSE Manager that registers client queues and broadcasts
    events to all active SSE browser connections.
    """
    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()

    def register_client(self):
        q = queue.Queue(maxsize=100)
        with self.lock:
            self.clients.append(q)
        return q

    def unregister_client(self, q):
        with self.lock:
            if q in self.clients:
                self.clients.remove(q)

    def broadcast(self, data, event_type=None):
        payload = ""
        if event_type:
            payload += f"event: {event_type}\n"
        payload += f"data: {json.dumps(data)}\n\n"

        with self.lock:
            # We copy list to avoid holding lock while putting to queue
            active_clients = list(self.clients)
            
        for q in active_clients:
            try:
                q.put_nowait(payload)
            except queue.Full:
                # Remove full/stale queue to clean up resources
                self.unregister_client(q)

sse_manager = SSEManager()
