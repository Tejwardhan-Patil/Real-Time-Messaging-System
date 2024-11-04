# API Documentation

## REST API Endpoints

### Authentication

- **POST /auth/login**
  - Authenticate user and provide a JWT token.

- **POST /auth/logout**
  - Logout user and invalidate session.

### Messaging

- **POST /messages/send**
  - Send a message to a specified channel or user.
  - **Body Parameters**:
    - `sender`: ID of the sender.
    - `recipient`: ID of the recipient.
    - `message`: The content of the message.
  
- **GET /messages/{channel_id}**
  - Retrieve all messages from a specified channel.

### Notifications

- **GET /notifications**
  - Retrieve real-time notifications for the user.

## WebSocket API

- **/ws/connect**
  - Establish a WebSocket connection for real-time messaging.
  
- **/ws/send**
  - Send a message over the WebSocket connection.

- **/ws/receive**
  - Receive messages in real time.

## Error Handling

- **400** Bad Request: Invalid input parameters.
- **401** Unauthorized: Invalid or missing JWT token.
- **404** Not Found: The requested resource was not found.
