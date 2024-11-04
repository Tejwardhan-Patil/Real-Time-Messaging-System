import unittest
import subprocess
import json
import os
from storage.relational_db import MessageStore
from storage.file_storage import LocalStorage

class StorageTests(unittest.TestCase):
    def setUp(self):
        # Setup for relational database
        self.relational_store = MessageStore(db_config={"host": "localhost", "user": "test", "password": "test", "db": "test_db"})

        # Setup for Local Storage
        self.local_storage = LocalStorage(storage_path="/tmp/test_storage")

        # Sample message
        self.sample_message = {
            "user_id": 1,
            "channel_id": 101,
            "message_content": "Test message",
            "timestamp": "2024-08-08T10:00:00Z"
        }

        # Paths to the Go and Scala binaries for MongoDB and Cassandra
        self.mongodb_binary = "/storage/nosql_db/mongodb_store"
        self.cassandra_binary = "/storage/nosql_db/cassandra_store"

    def test_relational_store_save_message(self):
        """Test saving a message to the relational store."""
        saved_message = self.relational_store.save_message(self.sample_message)
        self.assertEqual(saved_message['message_content'], self.sample_message['message_content'])
        self.assertIn('id', saved_message)

    def test_relational_store_retrieve_message(self):
        """Test retrieving a message from the relational store."""
        message_id = self.relational_store.save_message(self.sample_message)['id']
        retrieved_message = self.relational_store.retrieve_message(message_id)
        self.assertEqual(retrieved_message['id'], message_id)
        self.assertEqual(retrieved_message['message_content'], self.sample_message['message_content'])

    def _run_external_command(self, binary_path, command, input_data):
        """Helper method to run external Go/Scala scripts using subprocess."""
        try:
            result = subprocess.run(
                [binary_path, command],
                input=json.dumps(input_data).encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running {binary_path}: {e.stderr.decode('utf-8')}")
            return None

    def test_mongodb_store_save_message(self):
        """Test saving a message to MongoDB using external Go script."""
        saved_message = self._run_external_command(self.mongodb_binary, "save", self.sample_message)
        self.assertIsNotNone(saved_message)
        self.assertIn('_id', saved_message)
        self.assertEqual(saved_message['message_content'], self.sample_message['message_content'])

    def test_mongodb_store_retrieve_message(self):
        """Test retrieving a message from MongoDB using external Go script."""
        saved_message = self._run_external_command(self.mongodb_binary, "save", self.sample_message)
        message_id = saved_message['_id']
        retrieved_message = self._run_external_command(self.mongodb_binary, "retrieve", {"_id": message_id})
        self.assertEqual(retrieved_message['_id'], message_id)
        self.assertEqual(retrieved_message['message_content'], self.sample_message['message_content'])

    def test_cassandra_store_save_message(self):
        """Test saving a message to Cassandra using external Scala script."""
        saved_message = self._run_external_command(self.cassandra_binary, "save", self.sample_message)
        self.assertIsNotNone(saved_message)
        self.assertIn('message_id', saved_message)
        self.assertEqual(saved_message['message_content'], self.sample_message['message_content'])

    def test_cassandra_store_retrieve_message(self):
        """Test retrieving a message from Cassandra using external Scala script."""
        saved_message = self._run_external_command(self.cassandra_binary, "save", self.sample_message)
        message_id = saved_message['message_id']
        retrieved_message = self._run_external_command(self.cassandra_binary, "retrieve", {"message_id": message_id})
        self.assertEqual(retrieved_message['message_id'], message_id)
        self.assertEqual(retrieved_message['message_content'], self.sample_message['message_content'])

    def test_local_storage_save_message(self):
        """Test saving a message to local storage."""
        file_name = f"message_{self.sample_message['user_id']}_{self.sample_message['channel_id']}.txt"
        saved_message_path = self.local_storage.save_message(self.sample_message, file_name)
        self.assertTrue(self.local_storage.file_exists(saved_message_path))

    def test_local_storage_retrieve_message(self):
        """Test retrieving a message from local storage."""
        file_name = f"message_{self.sample_message['user_id']}_{self.sample_message['channel_id']}.txt"
        self.local_storage.save_message(self.sample_message, file_name)
        retrieved_message = self.local_storage.retrieve_message(file_name)
        self.assertEqual(retrieved_message['message_content'], self.sample_message['message_content'])

    def test_relational_store_delete_message(self):
        """Test deleting a message from the relational store."""
        message_id = self.relational_store.save_message(self.sample_message)['id']
        self.relational_store.delete_message(message_id)
        deleted_message = self.relational_store.retrieve_message(message_id)
        self.assertIsNone(deleted_message)

    def test_mongodb_store_delete_message(self):
        """Test deleting a message from MongoDB using external Go script."""
        saved_message = self._run_external_command(self.mongodb_binary, "save", self.sample_message)
        message_id = saved_message['_id']
        self._run_external_command(self.mongodb_binary, "delete", {"_id": message_id})
        deleted_message = self._run_external_command(self.mongodb_binary, "retrieve", {"_id": message_id})
        self.assertIsNone(deleted_message)

    def test_cassandra_store_delete_message(self):
        """Test deleting a message from Cassandra using external Scala script."""
        saved_message = self._run_external_command(self.cassandra_binary, "save", self.sample_message)
        message_id = saved_message['message_id']
        self._run_external_command(self.cassandra_binary, "delete", {"message_id": message_id})
        deleted_message = self._run_external_command(self.cassandra_binary, "retrieve", {"message_id": message_id})
        self.assertIsNone(deleted_message)

    def test_local_storage_delete_message(self):
        """Test deleting a message from local storage."""
        file_name = f"message_{self.sample_message['user_id']}_{self.sample_message['channel_id']}.txt"
        self.local_storage.save_message(self.sample_message, file_name)
        self.local_storage.delete_message(file_name)
        self.assertFalse(self.local_storage.file_exists(file_name))

    def test_bulk_save_messages(self):
        """Test saving multiple messages in bulk to the relational store."""
        messages = [self.sample_message for _ in range(10)]
        saved_messages = self.relational_store.bulk_save_messages(messages)
        self.assertEqual(len(saved_messages), 10)
        self.assertTrue(all(['id' in msg for msg in saved_messages]))

    def test_bulk_delete_messages(self):
        """Test deleting multiple messages in bulk from the relational store."""
        messages = [self.relational_store.save_message(self.sample_message) for _ in range(5)]
        message_ids = [msg['id'] for msg in messages]
        self.relational_store.bulk_delete_messages(message_ids)
        for msg_id in message_ids:
            self.assertIsNone(self.relational_store.retrieve_message(msg_id))

if __name__ == '__main__':
    unittest.main()