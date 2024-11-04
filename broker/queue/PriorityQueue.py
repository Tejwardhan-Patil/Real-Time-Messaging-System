import heapq
import threading
import time
from typing import Any, Tuple


class PriorityQueue:
    def __init__(self):
        # Initializes an empty priority queue
        self.queue = []
        self.lock = threading.Lock()
        self.counter = 0  # A counter to track insertion order for equal priority

    def enqueue(self, priority: int, message: Any):
        """Enqueue a message with a given priority."""
        with self.lock:
            # Uses a tuple of (priority, counter, message) to maintain order for same priority
            heapq.heappush(self.queue, (priority, self.counter, message))
            self.counter += 1

    def dequeue(self) -> Tuple[int, Any]:
        """Dequeue the highest priority message."""
        with self.lock:
            if self.is_empty():
                raise IndexError("Dequeue from an empty priority queue.")
            return heapq.heappop(self.queue)[1:]  # Return counter and message, ignoring priority

    def peek(self) -> Any:
        """Peek at the highest priority message without removing it."""
        with self.lock:
            if self.is_empty():
                return None
            return self.queue[0][2]  # Return the message without dequeuing it

    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self.queue) == 0

    def size(self) -> int:
        """Return the current size of the queue."""
        with self.lock:
            return len(self.queue)

    def clear(self):
        """Clear all items from the queue."""
        with self.lock:
            self.queue.clear()
            self.counter = 0


class Message:
    def __init__(self, content: str, sender: str, timestamp: float):
        self.content = content
        self.sender = sender
        self.timestamp = timestamp

    def __str__(self):
        return f"[{self.sender}]: {self.content} @ {time.ctime(self.timestamp)}"


class PriorityMessageQueue(PriorityQueue):
    def __init__(self):
        super().__init__()

    def enqueue_message(self, priority: int, message: Message):
        """Enqueue a message object with a given priority."""
        self.enqueue(priority, message)

    def dequeue_message(self) -> Message:
        """Dequeue the highest priority message."""
        return self.dequeue()[1]  # Return only the message, discard the counter

    def peek_message(self) -> Message:
        """Peek at the highest priority message without removing it."""
        return self.peek()

    def __str__(self):
        """String representation of the entire queue."""
        return "\n".join([str(item[2]) for item in self.queue])  # Print all messages in queue


# Usage of the PriorityQueue
def producer(queue: PriorityMessageQueue, message_count: int):
    """Simulates a producer generating messages."""
    for i in range(message_count):
        message = Message(
            content=f"Message {i}",
            sender=f"Producer-{i}",
            timestamp=time.time()
        )
        priority = i % 5  
        print(f"Producing message with priority {priority}: {message}")
        queue.enqueue_message(priority, message)
        time.sleep(1)  


def consumer(queue: PriorityMessageQueue):
    """Simulates a consumer processing messages from the queue."""
    while True:
        if not queue.is_empty():
            message = queue.dequeue_message()
            print(f"Consumed: {message}")
            time.sleep(2)  
        else:
            time.sleep(1)  


if __name__ == "__main__":
    # Create a shared priority message queue
    priority_queue = PriorityMessageQueue()

    # Create producer and consumer threads
    producer_thread = threading.Thread(target=producer, args=(priority_queue, 10))
    consumer_thread = threading.Thread(target=consumer, args=(priority_queue,))

    # Start the threads
    producer_thread.start()
    consumer_thread.start()

    # Wait for threads to finish
    producer_thread.join()
    consumer_thread.join()