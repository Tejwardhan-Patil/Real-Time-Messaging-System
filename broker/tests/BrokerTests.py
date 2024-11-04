import unittest
import subprocess
import os
from unittest.mock import MagicMock
from broker.queue.MessageQueue import MessageQueue
from broker.queue.PriorityQueue import PriorityQueue
from broker.protocols.WebSocketProtocol import WebSocketProtocol

class TestIntegrationWithSubprocess(unittest.TestCase):

    def setUp(self):
        # Setting up Python components
        self.message_queue = MessageQueue()
        self.websocket_protocol = WebSocketProtocol()

    def test_java_publisher_integration(self):
        # Simulate running the Java Publisher as a subprocess
        topic = "test_topic"
        message = "Test message for Java Publisher"
        
        publisher_process = subprocess.Popen(
            ['java', '-cp', 'broker/pubsub', 'Publisher', topic, message],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = publisher_process.communicate()
        
        self.assertEqual(publisher_process.returncode, 0, f"Java Publisher failed: {stderr.decode('utf-8')}")
        print(f"Publisher output: {stdout.decode('utf-8')}")

    def test_java_subscriber_integration(self):
        # Simulate running the Java Subscriber as a subprocess
        topic = "test_topic"
        
        subscriber_process = subprocess.Popen(
            ['java', '-cp', 'broker/pubsub', 'Subscriber', topic],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = subscriber_process.communicate()
        
        self.assertEqual(subscriber_process.returncode, 0, f"Java Subscriber failed: {stderr.decode('utf-8')}")
        print(f"Subscriber output: {stdout.decode('utf-8')}")
    
    def test_scala_rabbitmq_protocol_integration(self):
        # Simulate running the Scala RabbitMQ Protocol as a subprocess
        rabbitmq_process = subprocess.Popen(
            ['scala', 'broker/protocols/RabbitMQProtocol'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = rabbitmq_process.communicate()
        
        self.assertEqual(rabbitmq_process.returncode, 0, f"Scala RabbitMQ Protocol failed: {stderr.decode('utf-8')}")
        print(f"RabbitMQ Protocol output: {stdout.decode('utf-8')}")

    def test_message_queue_to_websocket(self):
        # Enqueue a message in the MessageQueue and send it through WebSocket
        message = "Integration test message"
        self.message_queue.enqueue(message)
        queue_message = self.message_queue.dequeue()
        self.assertEqual(queue_message, message)
        
        # Mock WebSocketProtocol sending the message
        self.websocket_protocol.open_connection = MagicMock(return_value=True)
        self.websocket_protocol.send_message = MagicMock(return_value=True)

        connection_result = self.websocket_protocol.open_connection("ws://test-url")
        self.assertTrue(connection_result)
        
        send_result = self.websocket_protocol.send_message("ws://test-url", queue_message)
        self.websocket_protocol.send_message.assert_called_with("ws://test-url", queue_message)
        self.assertTrue(send_result)


class TestEndToEndMessageFlow(unittest.TestCase):
    
    def test_end_to_end_flow(self):
        # Start the Java Publisher subprocess
        topic = "test_topic"
        message = "End-to-end message"
        
        publisher_process = subprocess.Popen(
            ['java', '-cp', 'broker/pubsub', 'Publisher', topic, message],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = publisher_process.communicate()
        self.assertEqual(publisher_process.returncode, 0, f"Java Publisher failed: {stderr.decode('utf-8')}")
        
        # Start the Java Subscriber subprocess
        subscriber_process = subprocess.Popen(
            ['java', '-cp', 'broker/pubsub', 'Subscriber', topic],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = subscriber_process.communicate()
        self.assertEqual(subscriber_process.returncode, 0, f"Java Subscriber failed: {stderr.decode('utf-8')}")
        
        # Start the Scala RabbitMQ Protocol subprocess
        rabbitmq_process = subprocess.Popen(
            ['scala', 'broker/protocols/RabbitMQProtocol'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = rabbitmq_process.communicate()
        self.assertEqual(rabbitmq_process.returncode, 0, f"Scala RabbitMQ Protocol failed: {stderr.decode('utf-8')}")
        
        print(f"Publisher output: {stdout.decode('utf-8')}")
        print(f"Subscriber output: {stdout.decode('utf-8')}")
        print(f"RabbitMQ Protocol output: {stdout.decode('utf-8')}")


if __name__ == '__main__':
    unittest.main()