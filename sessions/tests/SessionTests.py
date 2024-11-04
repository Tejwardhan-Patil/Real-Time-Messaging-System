import unittest
import subprocess
import json
from sessions.SessionManager import SessionManager
from sessions.distributed_sessions.SessionReplication import SessionReplication
from unittest.mock import patch

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = SessionManager()

    def test_create_session(self):
        user_id = "user_123"
        session_data = {"key": "value"}
        session = self.session_manager.create_session(user_id, session_data)

        self.assertEqual(session["user_id"], user_id)
        self.assertEqual(session["data"], session_data)

    def test_terminate_session(self):
        user_id = "user_123"
        session_data = {"key": "value"}
        session = self.session_manager.create_session(user_id, session_data)

        self.session_manager.terminate_session(user_id)
        session_terminated = self.session_manager.get_session(user_id)

        self.assertIsNone(session_terminated)

    def test_get_session(self):
        user_id = "user_456"
        session_data = {"status": "active"}
        self.session_manager.create_session(user_id, session_data)

        session = self.session_manager.get_session(user_id)

        self.assertIsNotNone(session)
        self.assertEqual(session["data"]["status"], "active")

    def test_multiple_sessions(self):
        user_id1 = "user_789"
        user_id2 = "user_987"
        session_data1 = {"key1": "value1"}
        session_data2 = {"key2": "value2"}

        self.session_manager.create_session(user_id1, session_data1)
        self.session_manager.create_session(user_id2, session_data2)

        session1 = self.session_manager.get_session(user_id1)
        session2 = self.session_manager.get_session(user_id2)

        self.assertEqual(session1["data"]["key1"], "value1")
        self.assertEqual(session2["data"]["key2"], "value2")

    @patch("sessions.heartbeat.HeartbeatMonitor")
    def test_session_heartbeat(self, MockHeartbeatMonitor):
        user_id = "user_123"
        session_data = {"heartbeat": "alive"}
        self.session_manager.create_session(user_id, session_data)

        heartbeat_monitor = MockHeartbeatMonitor.return_value
        heartbeat_monitor.ping.return_value = True

        self.assertTrue(heartbeat_monitor.ping())

    @patch.object(SessionManager, 'replicate_session')
    def test_session_replication(self, mock_replicate_session):
        user_id = "user_124"
        session_data = {"key": "value"}
        self.session_manager.create_session(user_id, session_data)

        mock_replicate_session.assert_called_with(user_id, session_data)

    def test_terminate_all_sessions(self):
        user_id1 = "user_789"
        user_id2 = "user_987"
        session_data1 = {"key1": "value1"}
        session_data2 = {"key2": "value2"}

        self.session_manager.create_session(user_id1, session_data1)
        self.session_manager.create_session(user_id2, session_data2)

        self.session_manager.terminate_all_sessions()

        session1 = self.session_manager.get_session(user_id1)
        session2 = self.session_manager.get_session(user_id2)

        self.assertIsNone(session1)
        self.assertIsNone(session2)

class TestPresenceService(unittest.TestCase):
    def setUp(self):
        self.presence_service_command = ["go", "run", "sessions/PresenceService.go"]

    def run_presence_service_command(self, action, user_id):
        process = subprocess.Popen(
            self.presence_service_command + [action, user_id],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stderr:
            raise RuntimeError(f"PresenceService error: {stderr.decode('utf-8')}")
        return json.loads(stdout.decode('utf-8'))

    def test_user_online(self):
        user_id = "user_123"
        response = self.run_presence_service_command("online", user_id)

        self.assertTrue(response["status"])
        self.assertEqual(response["user_id"], user_id)

    def test_user_offline(self):
        user_id = "user_456"
        self.run_presence_service_command("online", user_id)
        response = self.run_presence_service_command("offline", user_id)

        self.assertFalse(response["status"])
        self.assertEqual(response["user_id"], user_id)

    def test_broadcast_presence(self):
        user_id = "user_789"
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.communicate.return_value = (json.dumps({"status": True}).encode('utf-8'), b'')
            response = self.run_presence_service_command("broadcast", user_id)

            self.assertTrue(response["status"])
            mock_popen.assert_called()

    def test_get_all_online_users(self):
        user_id1 = "user_123"
        user_id2 = "user_456"
        self.run_presence_service_command("online", user_id1)
        self.run_presence_service_command("online", user_id2)

        process = subprocess.Popen(
            self.presence_service_command + ["list"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = process.communicate()
        online_users = json.loads(stdout.decode('utf-8'))

        self.assertIn(user_id1, online_users)
        self.assertIn(user_id2, online_users)

    def test_user_presence_status(self):
        user_id = "user_789"
        self.run_presence_service_command("online", user_id)

        response_online = self.run_presence_service_command("status", user_id)
        self.assertEqual(response_online["status"], "online")

        self.run_presence_service_command("offline", user_id)

        response_offline = self.run_presence_service_command("status", user_id)
        self.assertEqual(response_offline["status"], "offline")

    @patch("subprocess.Popen")
    def test_broadcast_presence_update(self, mock_popen):
        user_id = "user_123"
        mock_popen.return_value.communicate.return_value = (json.dumps({"status": True}).encode('utf-8'), b'')
        response = self.run_presence_service_command("broadcast", user_id)

        self.assertTrue(response["status"])
        mock_popen.assert_called()

class TestSessionReplication(unittest.TestCase):
    def setUp(self):
        self.replication_service = SessionReplication()

    @patch.object(SessionReplication, 'replicate_to_node')
    def test_replicate_session(self, mock_replicate_to_node):
        user_id = "user_123"
        session_data = {"key": "value"}

        self.replication_service.replicate_session(user_id, session_data)

        mock_replicate_to_node.assert_called_with(user_id, session_data)

    def test_replicate_to_multiple_nodes(self):
        user_id = "user_124"
        session_data = {"key": "value"}
        nodes = ["node1", "node2", "node3"]

        with patch.object(self.replication_service, 'replicate_to_node') as mock_replicate:
            self.replication_service.replicate_session_to_multiple_nodes(user_id, session_data, nodes)

            mock_replicate.assert_called()
            self.assertEqual(mock_replicate.call_count, len(nodes))

    def test_ensure_replication_integrity(self):
        user_id = "user_456"
        session_data = {"key": "value"}
        
        with patch.object(self.replication_service, 'verify_replication') as mock_verify:
            self.replication_service.replicate_session(user_id, session_data)

            mock_verify.assert_called_with(user_id, session_data)

if __name__ == "__main__":
    unittest.main()