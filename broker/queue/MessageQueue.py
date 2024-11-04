import threading
import time
import uuid
from queue import Queue, Empty

class Message:
    def __init__(self, content, priority=0):
        self.id = str(uuid.uuid4())
        self.content = content
        self.priority = priority
        self.timestamp = time.time()
        self.acknowledged = False

    def acknowledge(self):
        self.acknowledged = True

class MessageQueue:
    def __init__(self, max_size=1000):
        self.queue = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.pending_ack = {}
        self.ack_timeout = 30  # seconds
        self.cleanup_interval = 10  # seconds
        self._cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        self._cleanup_thread.start()

    def enqueue(self, content, priority=0):
        message = Message(content, priority)
        try:
            self.queue.put_nowait(message)
            print(f"Enqueued message: {message.id}")
        except:
            print(f"Queue is full, cannot enqueue message: {message.id}")
        return message

    def dequeue(self):
        try:
            message = self.queue.get(timeout=1)
            with self.lock:
                self.pending_ack[message.id] = message
            print(f"Dequeued message: {message.id}")
            return message
        except Empty:
            print("Queue is empty, no message to dequeue.")
            return None

    def acknowledge(self, message_id):
        with self.lock:
            if message_id in self.pending_ack:
                message = self.pending_ack.pop(message_id)
                message.acknowledge()
                print(f"Message {message_id} acknowledged.")
                return True
            else:
                print(f"Message {message_id} not found in pending acknowledgments.")
                return False

    def requeue_unacknowledged(self):
        with self.lock:
            now = time.time()
            for message_id, message in list(self.pending_ack.items()):
                if not message.acknowledged and (now - message.timestamp) > self.ack_timeout:
                    self.pending_ack.pop(message_id)
                    self.queue.put_nowait(message)
                    print(f"Requeued unacknowledged message: {message.id}")

    def _cleanup_task(self):
        while True:
            time.sleep(self.cleanup_interval)
            self.requeue_unacknowledged()

    def get_queue_size(self):
        return self.queue.qsize()

    def get_pending_ack_size(self):
        with self.lock:
            return len(self.pending_ack)

# Publisher and Subscriber classes for working with the queue
class Publisher:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def publish(self, message_content, priority=0):
        message = self.message_queue.enqueue(content=message_content, priority=priority)
        return message

class Subscriber:
    def __init__(self, message_queue):
        self.message_queue = message_queue

    def receive_message(self):
        message = self.message_queue.dequeue()
        if message:
            print(f"Subscriber received message: {message.content}")
            return message
        else:
            return None

    def acknowledge_message(self, message_id):
        success = self.message_queue.acknowledge(message_id)
        return success

# Test the functionality
def publisher_task(publisher, count):
    for i in range(count):
        publisher.publish(f"Message {i+1}")
        time.sleep(1)

def subscriber_task(subscriber, count):
    for _ in range(count):
        message = subscriber.receive_message()
        if message:
            # Simulate processing the message
            time.sleep(2)
            subscriber.acknowledge_message(message.id)

if __name__ == "__main__":
    # Create the message queue
    message_queue = MessageQueue(max_size=10)

    # Create publisher and subscriber
    publisher = Publisher(message_queue)
    subscriber = Subscriber(message_queue)

    # Run publisher and subscriber in separate threads
    publisher_thread = threading.Thread(target=publisher_task, args=(publisher, 5))
    subscriber_thread = threading.Thread(target=subscriber_task, args=(subscriber, 5))

    publisher_thread.start()
    subscriber_thread.start()

    publisher_thread.join()
    subscriber_thread.join()

    print("Test completed.")