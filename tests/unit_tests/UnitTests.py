import unittest
import subprocess
from storage.relational_db.MessageStore import MessageStore
from sessions.SessionManager import SessionManager
from auth.JWTAuth import JWTAuth
from api.websocket_gateway.ConnectionManager import ConnectionManager
from broker.queue.MessageQueue import MessageQueue
from broker.queue.PriorityQueue import PriorityQueue

class TestMessageStore(unittest.TestCase):
    def setUp(self):
        self.message_store = MessageStore()

    def test_store_message(self):
        message = {"user": "Person", "content": "Hello!"}
        result = self.message_store.store_message(message)
        self.assertTrue(result)

    def test_retrieve_message(self):
        message_id = "msg123"
        message = self.message_store.retrieve_message(message_id)
        self.assertEqual(message['id'], message_id)

    def test_delete_message(self):
        message_id = "msg123"
        result = self.message_store.delete_message(message_id)
        self.assertTrue(result)

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = SessionManager()

    def test_create_session(self):
        session = self.session_manager.create_session("Person1")
        self.assertIn("session_id", session)

    def test_terminate_session(self):
        session_id = "sess123"
        result = self.session_manager.terminate_session(session_id)
        self.assertTrue(result)

    def test_is_session_active(self):
        session_id = "sess123"
        result = self.session_manager.is_session_active(session_id)
        self.assertTrue(result)

class TestJWTAuth(unittest.TestCase):
    def setUp(self):
        self.auth = JWTAuth()

    def test_generate_token(self):
        user_data = {"username": "Person1", "role": "admin"}
        token = self.auth.generate_token(user_data)
        self.assertIsNotNone(token)

    def test_validate_token(self):
        token = "valid.jwt.token"
        result = self.auth.validate_token(token)
        self.assertTrue(result)

    def test_invalidate_token(self):
        token = "valid.jwt.token"
        result = self.auth.invalidate_token(token)
        self.assertTrue(result)

class TestFCMService(unittest.TestCase):
    def setUp(self):
        self.java_service = "java -jar FCMService.jar"

    def test_send_notification(self):
        notification = '{"title": "New Message", "body": "You\'ve got mail!"}'
        command = f"{self.java_service} send_notification device_token {notification}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.assertIn("success", result.stdout)

    def test_send_bulk_notifications(self):
        notifications = '[{"title": "Hello", "body": "World!"}, {"title": "New", "body": "Message"}]'
        command = f"{self.java_service} send_bulk_notifications [device1,device2] {notifications}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.assertIn("success", result.stdout)

class TestAPNSService(unittest.TestCase):
    def setUp(self):
        self.go_service = "./APNSService"

    def test_send_notification(self):
        notification = '{"title": "New Update", "body": "Check it out!"}'
        command = f"{self.go_service} send_notification device_token {notification}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.assertIn("success", result.stdout)

class TestConnectionManager(unittest.TestCase):
    def setUp(self):
        self.connection_manager = ConnectionManager()

    def test_add_connection(self):
        user_id = "user123"
        connection_id = "conn123"
        result = self.connection_manager.add_connection(user_id, connection_id)
        self.assertTrue(result)

    def test_remove_connection(self):
        connection_id = "conn123"
        result = self.connection_manager.remove_connection(connection_id)
        self.assertTrue(result)

    def test_broadcast_message(self):
        message = {"type": "text", "content": "This is a test!"}
        result = self.connection_manager.broadcast_message(message)
        self.assertTrue(result)

class TestMessageQueue(unittest.TestCase):
    def setUp(self):
        self.queue = MessageQueue()

    def test_enqueue_message(self):
        message = {"user": "Person", "content": "Queue message"}
        result = self.queue.enqueue_message(message)
        self.assertTrue(result)

    def test_dequeue_message(self):
        result = self.queue.dequeue_message()
        self.assertIsNotNone(result)

class TestPriorityQueue(unittest.TestCase):
    def setUp(self):
        self.priority_queue = PriorityQueue()

    def test_enqueue_priority_message(self):
        message = {"user": "Person", "content": "Priority message", "priority": 1}
        result = self.priority_queue.enqueue_priority_message(message)
        self.assertTrue(result)

    def test_dequeue_priority_message(self):
        result = self.priority_queue.dequeue_priority_message()
        self.assertIsNotNone(result)

class TestNotifications(unittest.TestCase):
    def test_push_notification(self):
        fcm_service = "java -jar FCMService.jar"
        apns_service = "./APNSService"

        notification = '{"title": "Welcome", "body": "Thanks for signing up!"}'

        fcm_command = f"{fcm_service} send_notification fcm_token {notification}"
        apns_command = f"{apns_service} send_notification apns_token {notification}"

        fcm_result = subprocess.run(fcm_command, shell=True, capture_output=True, text=True)
        apns_result = subprocess.run(apns_command, shell=True, capture_output=True, text=True)

        self.assertIn("success", fcm_result.stdout)
        self.assertIn("success", apns_result.stdout)

if __name__ == '__main__':
    unittest.main()