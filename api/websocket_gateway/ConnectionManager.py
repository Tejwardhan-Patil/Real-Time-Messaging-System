import asyncio
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConnectionManager")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.user_rooms: Dict[str, List[str]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room: str, user_id: str):
        await websocket.accept()
        self.active_connections[room].append(websocket)
        self.user_rooms[user_id].append(room)
        logger.info(f"User {user_id} connected to room {room}")

    def disconnect(self, websocket: WebSocket, room: str, user_id: str):
        if websocket in self.active_connections[room]:
            self.active_connections[room].remove(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]
        self.user_rooms[user_id].remove(room)
        logger.info(f"User {user_id} disconnected from room {room}")

    async def broadcast(self, message: str, room: str):
        logger.info(f"Broadcasting message to room {room}")
        connections = self.active_connections.get(room, [])
        for connection in connections:
            await connection.send_text(message)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    def get_rooms_for_user(self, user_id: str) -> List[str]:
        return self.user_rooms.get(user_id, [])

    def get_connections_for_room(self, room: str) -> List[WebSocket]:
        return self.active_connections.get(room, [])

# FastAPI WebSocket endpoint
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

connection_manager = ConnectionManager()

@app.websocket("/ws/{room}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room: str, user_id: str):
    await connection_manager.connect(websocket, room, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.broadcast(f"{user_id}: {data}", room)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room, user_id)
        await connection_manager.broadcast(f"{user_id} left the room.", room)

# Authentication Dependency
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify the token and return the current user
    if token == "valid_token":
        return {"user_id": "user123"}
    raise HTTPException(status_code=401, detail="Invalid token")

# WebSocket endpoint with authentication
@app.websocket("/ws/auth/{room}")
async def websocket_endpoint_auth(websocket: WebSocket, room: str, token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    await connection_manager.connect(websocket, room, user["user_id"])
    try:
        while True:
            data = await websocket.receive_text()
            await connection_manager.broadcast(f"{user['user_id']}: {data}", room)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, room, user["user_id"])
        await connection_manager.broadcast(f"{user['user_id']} left the room.", room)

# Background task to periodically send pings to connected clients
@app.on_event("startup")
async def start_ping_task():
    asyncio.create_task(ping_clients())

async def ping_clients():
    while True:
        await asyncio.sleep(30)
        logger.info("Pinging all connected clients")
        for room, connections in connection_manager.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_text("ping")
                except Exception as e:
                    logger.error(f"Failed to ping client: {str(e)}")

# Manage room subscriptions
@app.post("/subscribe/{room}/{user_id}")
async def subscribe_user_to_room(room: str, user_id: str):
    rooms = connection_manager.get_rooms_for_user(user_id)
    if room not in rooms:
        connection_manager.user_rooms[user_id].append(room)
        return {"message": f"User {user_id} subscribed to {room}"}
    else:
        return {"message": f"User {user_id} is already subscribed to {room}"}

@app.post("/unsubscribe/{room}/{user_id}")
async def unsubscribe_user_from_room(room: str, user_id: str):
    rooms = connection_manager.get_rooms_for_user(user_id)
    if room in rooms:
        connection_manager.user_rooms[user_id].remove(room)
        return {"message": f"User {user_id} unsubscribed from {room}"}
    else:
        return {"message": f"User {user_id} is not subscribed to {room}"}

# Handle message broadcasts through an API endpoint
@app.post("/broadcast/{room}")
async def broadcast_message(room: str, message: str):
    await connection_manager.broadcast(message, room)
    return {"message": f"Broadcasted to room {room}"}

# Disconnect all users from a room
@app.post("/disconnect_all/{room}")
async def disconnect_all_from_room(room: str):
    connections = connection_manager.get_connections_for_room(room)
    for connection in connections:
        await connection.close()
    connection_manager.active_connections.pop(room, None)
    return {"message": f"Disconnected all users from {room}"}

# Managing specific user messaging
@app.post("/send_personal_message/{room}/{user_id}")
async def send_personal_message(room: str, user_id: str, message: str):
    connections = connection_manager.get_connections_for_room(room)
    for connection in connections:
        try:
            await connection_manager.send_personal_message(message, connection)
        except Exception as e:
            logger.error(f"Failed to send personal message: {str(e)}")
    return {"message": f"Personal message sent to user {user_id}"}