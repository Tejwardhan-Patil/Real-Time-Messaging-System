import asyncio
import websockets
import json
import logging

class WebSocketProtocol:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.logger = logging.getLogger('WebSocketProtocol')
        logging.basicConfig(level=logging.INFO)

    async def register(self, websocket):
        """Registers a new client connection."""
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")

    async def unregister(self, websocket):
        """Unregisters a client connection."""
        self.clients.remove(websocket)
        self.logger.info(f"Client disconnected: {websocket.remote_address}")

    async def send_message(self, message):
        """Broadcast a message to all connected clients."""
        if self.clients:
            message_data = json.dumps(message)
            await asyncio.wait([client.send(message_data) for client in self.clients])

    async def receive_message(self, websocket):
        """Handles receiving a message from a client."""
        try:
            async for message in websocket:
                data = json.loads(message)
                self.logger.info(f"Received message: {data}")
                await self.handle_message(websocket, data)
        except websockets.ConnectionClosed as e:
            self.logger.error(f"Connection closed: {e}")

    async def handle_message(self, websocket, message):
        """Process and handle the message from the client."""
        if message['type'] == 'ping':
            response = {'type': 'pong', 'message': 'Pong!'}
            await websocket.send(json.dumps(response))
        elif message['type'] == 'broadcast':
            await self.send_message(message)
        else:
            self.logger.warning(f"Unknown message type: {message['type']}")

    async def handler(self, websocket, path):
        """Main handler for managing WebSocket connections."""
        await self.register(websocket)
        try:
            await self.receive_message(websocket)
        finally:
            await self.unregister(websocket)

    async def start_server(self):
        """Starts the WebSocket server."""
        self.logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Run forever

if __name__ == '__main__':
    protocol = WebSocketProtocol()
    try:
        asyncio.run(protocol.start_server())
    except KeyboardInterrupt:
        protocol.logger.info("Server stopped by user")

# ------------------ WebSocket Client ------------------

class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.logger = logging.getLogger('WebSocketClient')
        logging.basicConfig(level=logging.INFO)

    async def connect(self):
        """Establishes a WebSocket connection to the server."""
        async with websockets.connect(self.uri) as websocket:
            self.logger.info(f"Connected to server at {self.uri}")
            await self.send_message(websocket, {'type': 'ping'})
            await self.listen(websocket)

    async def send_message(self, websocket, message):
        """Send a message to the WebSocket server."""
        self.logger.info(f"Sending message: {message}")
        await websocket.send(json.dumps(message))

    async def listen(self, websocket):
        """Listens for messages from the server."""
        try:
            async for message in websocket:
                data = json.loads(message)
                self.logger.info(f"Received message: {data}")
                await self.handle_message(data)
        except websockets.ConnectionClosed as e:
            self.logger.error(f"Connection closed: {e}")

    async def handle_message(self, message):
        """Processes messages from the server."""
        if message['type'] == 'pong':
            self.logger.info("Received Pong from server!")
        else:
            self.logger.warning(f"Unknown message type: {message['type']}")

if __name__ == '__main__':
    client = WebSocketClient('ws://localhost:8765')
    try:
        asyncio.run(client.connect())
    except KeyboardInterrupt:
        client.logger.info("Client stopped by user")