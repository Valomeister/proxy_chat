import traceback
from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:

    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(
        self,
        order_id: int,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.connections[order_id].append(websocket)

    def disconnect(
        self,
        order_id: int,
        websocket: WebSocket,
    ):
        self.connections[order_id].remove(websocket)

        if not self.connections[order_id]:
            del self.connections[order_id]

    async def broadcast(
        self,
        order_id: int,
        event: dict,
    ):
        dead = []

        for ws in self.connections.get(order_id, []):

            try:
                await ws.send_json(event)

            except Exception:
                traceback.print_exc()
                dead.append(ws)

        for ws in dead:
            self.disconnect(order_id, ws)


ws_manager = ConnectionManager()