import json
import redis
import threading
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class RedisSessionReplication:
    """
    Redis-based session replication for fault tolerance.
    This class ensures session data is replicated across multiple Redis nodes.
    """

    def __init__(self, redis_nodes: list):
        """
        Initialize the session replication with a list of Redis nodes.
        :param redis_nodes: List of Redis nodes as (host, port) tuples
        """
        self.redis_clients = [redis.Redis(host=node[0], port=node[1]) for node in redis_nodes]
        self.session_data = {}
        self.lock = threading.Lock()

    def create_session(self, user_id: str, data: dict, expiry: int = 3600) -> str:
        """
        Creates a new session for a user and replicates it across Redis nodes.
        :param user_id: Unique identifier for the user
        :param data: Session data to store
        :param expiry: Time to live for session (seconds)
        :return: Session ID
        """
        session_id = f"session:{user_id}"
        session_payload = json.dumps(data)

        # Store the session in Redis
        with self.lock:
            for redis_client in self.redis_clients:
                redis_client.set(session_id, session_payload, ex=expiry)

        logging.info(f"Session created for user {user_id} with session ID {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session data from any Redis node.
        :param session_id: Session ID
        :return: Session data as dictionary, or None if not found
        """
        for redis_client in self.redis_clients:
            session_payload = redis_client.get(session_id)
            if session_payload:
                logging.info(f"Session {session_id} retrieved from Redis.")
                return json.loads(session_payload)
        logging.warning(f"Session {session_id} not found in any Redis node.")
        return None

    def update_session(self, session_id: str, data: dict) -> bool:
        """
        Updates an existing session and replicates the changes.
        :param session_id: Session ID
        :param data: Updated session data
        :return: True if session update was successful, False otherwise
        """
        session_payload = json.dumps(data)

        with self.lock:
            for redis_client in self.redis_clients:
                result = redis_client.set(session_id, session_payload)
                if not result:
                    logging.error(f"Failed to update session {session_id} in Redis.")
                    return False
        logging.info(f"Session {session_id} updated successfully.")
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Deletes a session across all Redis nodes.
        :param session_id: Session ID
        :return: True if session deletion was successful, False otherwise
        """
        with self.lock:
            for redis_client in self.redis_clients:
                redis_client.delete(session_id)

        logging.info(f"Session {session_id} deleted from all Redis nodes.")
        return True

    def replicate_session(self, session_id: str) -> None:
        """
        Ensures session data is replicated to all Redis nodes.
        This function is intended for use in a multi-threaded environment.
        :param session_id: Session ID
        """
        session_data = self.get_session(session_id)
        if session_data:
            self.update_session(session_id, session_data)
            logging.info(f"Session {session_id} replicated across nodes.")

class SessionMonitor:
    """
    Session monitor to periodically check and replicate sessions.
    """
    
    def __init__(self, session_manager: RedisSessionReplication, interval: int = 60):
        """
        Initialize the monitor.
        :param session_manager: The session replication manager
        :param interval: Time interval to check sessions for replication
        """
        self.session_manager = session_manager
        self.interval = interval
        self.active = True
        self.thread = threading.Thread(target=self.monitor_sessions)
    
    def start_monitoring(self) -> None:
        """
        Starts the session monitoring thread.
        """
        self.thread.start()
        logging.info("Session monitoring started.")
    
    def stop_monitoring(self) -> None:
        """
        Stops the session monitoring thread.
        """
        self.active = False
        self.thread.join()
        logging.info("Session monitoring stopped.")
    
    def monitor_sessions(self) -> None:
        """
        Periodically monitors sessions and ensures replication.
        """
        while self.active:
            logging.info("Checking for sessions to replicate...")
            with self.session_manager.lock:
                for session_id in self.session_manager.session_data:
                    self.session_manager.replicate_session(session_id)
            time.sleep(self.interval)

# Simulating a distributed Redis environment with multiple nodes
redis_nodes = [("redis-node1", 6379), ("redis-node2", 6379), ("redis-node3", 6379)]
session_manager = RedisSessionReplication(redis_nodes)

# Simulating session creation and replication
session_id_1 = session_manager.create_session("user1", {"username": "person1", "email": "person1@website.com"})
session_id_2 = session_manager.create_session("user2", {"username": "person2", "email": "person2@website.com"})

# Retrieve sessions to test replication
session_data_1 = session_manager.get_session(session_id_1)
session_data_2 = session_manager.get_session(session_id_2)

# Update a session and replicate changes
session_manager.update_session(session_id_1, {"username": "person1_updated", "email": "person1@website.com"})

# Monitor the sessions periodically to ensure replication
session_monitor = SessionMonitor(session_manager, interval=30)
session_monitor.start_monitoring()

# Deleting a session
session_manager.delete_session(session_id_2)

# Stop the monitoring after some time
time.sleep(180)  # Let the monitor run for 3 minutes
session_monitor.stop_monitoring()