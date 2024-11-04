import time
import multiprocessing
import random
import subprocess
import requests
from queue import Queue
from threading import Thread
from api.rest_api.API import Routes 
from broker.queue.MessageQueue import MessageQueue  
from sessions.SessionManager import SessionManager
from scalability.load_balancer.HAProxyLB import HAProxyLB

# Constants for the test
NUM_USERS = 1000
NUM_MESSAGES = 10000
MESSAGE_LENGTH = 256
MESSAGE_QUEUE_SIZE = 5000
NUM_THREADS = 10

# Function to simulate user behavior: sending and receiving messages using Java Publisher and Subscriber
def simulate_user_behavior(user_id, message_queue):
    session = SessionManager.create_session(user_id)
    
    for _ in range(NUM_MESSAGES):
        # Simulate publishing a message using Java Publisher
        message = f"User {user_id}: " + ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=MESSAGE_LENGTH))
        subprocess.run(["java", "-cp", "broker/pubsub/Publisher", "Publisher", message], check=True)
        
        # Simulate receiving a message using Java Subscriber
        result = subprocess.run(["java", "-cp", "broker/pubsub/Subscriber", "Subscriber"], check=True, capture_output=True, text=True)
        received_message = result.stdout.strip()
        
        # Put the received message into the message queue
        message_queue.put(received_message)

# Function to stress test message queuing system
def stress_test_message_queue():
    message_queue = Queue(maxsize=MESSAGE_QUEUE_SIZE)

    # Test message publishing under load
    for i in range(NUM_MESSAGES):
        message = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=MESSAGE_LENGTH))
        message_queue.put(message)
        if i % 1000 == 0:
            print(f"Enqueued {i} messages")

    # Test message consumption under load
    for i in range(NUM_MESSAGES):
        message = message_queue.get()
        if i % 1000 == 0:
            print(f"Dequeued {i} messages")

# Function to load test the session management under heavy user load
def load_test_session_management():
    session_manager = SessionManager()

    def create_and_destroy_sessions(user_id):
        session = session_manager.create_session(user_id)
        session_manager.destroy_session(user_id)

    pool = multiprocessing.Pool(processes=NUM_THREADS)

    for user_id in range(NUM_USERS):
        pool.apply_async(create_and_destroy_sessions, args=(user_id,))
    
    pool.close()
    pool.join()
    print(f"All {NUM_USERS} user sessions created and destroyed successfully.")

# Function to test load balancing under HTTP/WS traffic
def load_balancer_test():
    haproxy_lb = HAProxyLB()

    def send_http_requests(user_id):
        for _ in range(100):
            response = requests.get(Routes.user_messages(user_id))
            if response.status_code != 200:
                print(f"Request failed for user {user_id}")
            else:
                print(f"Request successful for user {user_id}")

    threads = []
    for user_id in range(NUM_USERS):
        t = Thread(target=send_http_requests, args=(user_id,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("HTTP load balancer test completed successfully.")

# Function to simulate a large number of concurrent users sending messages
def concurrent_user_simulation():
    message_queue = Queue()

    def user_thread(user_id):
        simulate_user_behavior(user_id, message_queue)

    threads = []
    for user_id in range(NUM_USERS):
        t = Thread(target=user_thread, args=(user_id,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("Concurrent user simulation completed.")

# Main function to run scalability tests
if __name__ == "__main__":
    start_time = time.time()

    # Run each test
    print("Starting stress test for message queue...")
    stress_test_message_queue()

    print("Starting load test for session management...")
    load_test_session_management()

    print("Starting load balancer test...")
    load_balancer_test()

    print("Starting concurrent user simulation...")
    concurrent_user_simulation()

    end_time = time.time()
    print(f"Scalability tests completed in {end_time - start_time} seconds.")