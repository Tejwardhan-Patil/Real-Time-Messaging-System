from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict
from uuid import UUID, uuid4
from datetime import datetime
import asyncio

app = FastAPI()

# Models for API requests and responses

class Message(BaseModel):
    id: UUID = uuid4()
    sender: str
    receiver: str
    content: str
    timestamp: datetime = datetime.utcnow()

class User(BaseModel):
    username: str
    status: str

class Channel(BaseModel):
    name: str
    members: List[str] = []

# In-memory storage
users = []
messages = []
channels = []
active_connections: Dict[str, WebSocket] = {}

# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

# Routes

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "OK"}

@app.post("/users", response_model=User, tags=["Users"])
async def create_user(user: User):
    if any(u['username'] == user.username for u in users):
        raise HTTPException(status_code=400, detail="Username already exists")
    users.append(user.dict())
    return user

@app.get("/users", response_model=List[User], tags=["Users"])
async def list_users():
    return users

@app.post("/channels", response_model=Channel, tags=["Channels"])
async def create_channel(channel: Channel):
    if any(c['name'] == channel.name for c in channels):
        raise HTTPException(status_code=400, detail="Channel already exists")
    channels.append(channel.dict())
    return channel

@app.get("/channels", response_model=List[Channel], tags=["Channels"])
async def list_channels():
    return channels

@app.post("/channels/{channel_name}/messages", response_model=Message, tags=["Messages"])
async def send_message(channel_name: str, message: Message):
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if message.sender not in channel['members']:
        raise HTTPException(status_code=403, detail="Sender not a member of this channel")
    
    messages.append(message.dict())
    return message

@app.get("/channels/{channel_name}/messages", response_model=List[Message], tags=["Messages"])
async def get_channel_messages(channel_name: str):
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    channel_messages = [m for m in messages if m['receiver'] == channel_name]
    return channel_messages

@app.get("/messages/{user}", response_model=List[Message], tags=["Messages"])
async def get_user_messages(user: str):
    user_messages = [m for m in messages if m['receiver'] == user or m['sender'] == user]
    return user_messages

@app.post("/channels/{channel_name}/join", tags=["Channels"])
async def join_channel(channel_name: str, user: str):
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if user not in channel['members']:
        channel['members'].append(user)
    return {"message": f"{user} joined {channel_name}"}

@app.post("/channels/{channel_name}/leave", tags=["Channels"])
async def leave_channel(channel_name: str, user: str):
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    if user in channel['members']:
        channel['members'].remove(user)
    return {"message": f"{user} left {channel_name}"}

@app.delete("/users/{username}", tags=["Users"])
async def delete_user(username: str):
    global users
    users = [u for u in users if u['username'] != username]
    return {"message": f"User {username} deleted"}

@app.delete("/channels/{channel_name}", tags=["Channels"])
async def delete_channel(channel_name: str):
    global channels
    channels = [c for c in channels if c['name'] != channel_name]
    return {"message": f"Channel {channel_name} deleted"}

@app.delete("/channels/{channel_name}/messages", tags=["Messages"])
async def delete_channel_messages(channel_name: str):
    global messages
    messages = [m for m in messages if m['receiver'] != channel_name]
    return {"message": f"All messages in {channel_name} deleted"}

# WebSocket connection manager for real-time messaging
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        if username not in self.active_connections:
            self.active_connections[username] = []
        self.active_connections[username].append(websocket)

    async def disconnect(self, websocket: WebSocket, username: str):
        self.active_connections[username].remove(websocket)
        if len(self.active_connections[username]) == 0:
            del self.active_connections[username]

    async def broadcast(self, username: str, message: str):
        if username in self.active_connections:
            for connection in self.active_connections[username]:
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(username, f"{username}: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, username)
        await manager.broadcast(username, f"{username} left the chat")