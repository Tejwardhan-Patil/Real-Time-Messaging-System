import unittest
import json
import subprocess
from api.rest_api.API import app 
from api.websocket_gateway.ConnectionManager import ConnectionManager
from auth.JWTAuth import JWTAuth
from storage.relational_db.MessageStore import MessageStore

class APITests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.auth_service = JWTAuth()
        cls.connection_manager = ConnectionManager()
        cls.message_store = MessageStore()

    def test_api_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json.get("status"), "ok")

    def test_user_login(self):
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = self.client.post("/auth/login", data=json.dumps(login_data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        token = response.json.get("token")
        self.assertIsNotNone(token)

    def test_invalid_login(self):
        login_data = {
            "username": "wrong_user",
            "password": "wrong_password"
        }
        response = self.client.post("/auth/login", data=json.dumps(login_data), content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json.get("message"), "Invalid credentials")

    def test_message_sending(self):
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = self.client.post("/auth/login", data=json.dumps(login_data), content_type="application/json")
        token = response.json.get("token")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        message_data = {
            "recipient_id": "user2",
            "message": "Hello, this is a test message!"
        }
        response = self.client.post("/messages/send", data=json.dumps(message_data), headers=headers, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json.get("status"), "message_sent")

    def test_retrieve_messages(self):
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = self.client.post("/auth/login", data=json.dumps(login_data), content_type="application/json")
        token = response.json.get("token")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = self.client.get("/messages/retrieve", headers=headers)
        self.assertEqual(response.status_code, 200)
        messages = response.json.get("messages")
        self.assertIsInstance(messages, list)

    def test_message_store(self):
        message = {
            "sender_id": "user1",
            "recipient_id": "user2",
            "message": "Test storage message"
        }
        result = self.message_store.store_message(message)
        self.assertTrue(result)

        stored_message = self.message_store.get_message(message["sender_id"], message["recipient_id"])
        self.assertEqual(stored_message["message"], "Test storage message")

    def test_jwt_token_validation(self):
        token = self.auth_service.generate_token({"user_id": "test_user"})
        is_valid = self.auth_service.validate_token(token)
        self.assertTrue(is_valid)

    def test_jwt_token_invalid(self):
        is_valid = self.auth_service.validate_token("invalid_token")
        self.assertFalse(is_valid)

    def test_websocket_connection(self):
        result = self.connection_manager.connect_user("user1", "connection_id_123")
        self.assertTrue(result)

        user_connected = self.connection_manager.is_user_connected("user1")
        self.assertTrue(user_connected)

    def test_websocket_disconnection(self):
        result = self.connection_manager.disconnect_user("user1")
        self.assertTrue(result)

        user_connected = self.connection_manager.is_user_connected("user1")
        self.assertFalse(user_connected)

    def test_push_notification(self):
        notification_data = {
            "title": "Test Notification",
            "body": "This is a test push notification.",
            "recipient_token": "user_device_token"
        }
        result = self.send_push_notification(notification_data)
        self.assertTrue(result)

    def send_push_notification(self, notification_data):
        try:
            # Call the Java FCM service using subprocess
            command = [
                "java", 
                "-cp", "notifications/push_notifications/FCMService.jar", 
                "FCMService",
                json.dumps(notification_data)
            ]
            process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if process.returncode == 0:
                return process.stdout.strip() == "success"
            else:
                print(f"Error: {process.stderr}")
                return False
        except Exception as e:
            print(f"Exception while sending push notification: {str(e)}")
            return False

    def test_api_key_generation(self):
        response = self.client.post("/api_key/generate")
        self.assertEqual(response.status_code, 200)
        api_key = response.json.get("api_key")
        self.assertIsNotNone(api_key)

    def test_invalid_endpoint(self):
        response = self.client.get("/invalid/endpoint")
        self.assertEqual(response.status_code, 404)

    def test_integration_websocket_and_rest(self):
        # Simulate login and message sending via REST API
        login_data = {
            "username": "test_user",
            "password": "test_password"
        }
        response = self.client.post("/auth/login", data=json.dumps(login_data), content_type="application/json")
        token = response.json.get("token")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        message_data = {
            "recipient_id": "user2",
            "message": "Test message via API"
        }
        response = self.client.post("/messages/send", data=json.dumps(message_data), headers=headers, content_type="application/json")
        self.assertEqual(response.status_code, 200)

        # Check if the message is received over WebSocket
        result = self.connection_manager.is_user_connected("user2")
        self.assertTrue(result)

    def test_user_presence(self):
        result = self.connection_manager.is_user_connected("user1")
        self.assertTrue(result)

    @classmethod
    def tearDownClass(cls):
        cls.connection_manager.disconnect_all_users()
        cls.message_store.clear_all_messages()

if __name__ == "__main__":
    unittest.main()