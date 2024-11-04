import unittest
import subprocess
import socket
import ssl
import requests
from security.encryption.MessageEncryption import encrypt_message, decrypt_message
from security.auditing.AuditLog import AuditLog

class TestMessageEncryption(unittest.TestCase):
    def setUp(self):
        self.sample_message = "This is a test message."
        self.encryption_key = "test_encryption_key"

    def test_message_encryption(self):
        encrypted_message = encrypt_message(self.sample_message, self.encryption_key)
        self.assertNotEqual(self.sample_message, encrypted_message, "Encryption failed")
    
    def test_message_decryption(self):
        encrypted_message = encrypt_message(self.sample_message, self.encryption_key)
        decrypted_message = decrypt_message(encrypted_message, self.encryption_key)
        self.assertEqual(self.sample_message, decrypted_message, "Decryption failed")

    def test_decrypt_with_invalid_key(self):
        encrypted_message = encrypt_message(self.sample_message, self.encryption_key)
        with self.assertRaises(Exception):
            decrypt_message(encrypted_message, "invalid_key")

class TestDDoSProtection(unittest.TestCase):
    def test_basic_ddos_protection(self):
        result = subprocess.run(['go', 'run', 'security/detection/DDoSProtection.go', 'check', '192.168.1.1', '100'],
                                capture_output=True, text=True)
        self.assertIn('true', result.stdout, "DDoS protection failed")

    def test_excessive_traffic(self):
        result = subprocess.run(['go', 'run', 'security/detection/DDoSProtection.go', 'check', '192.168.1.1', '10000'],
                                capture_output=True, text=True)
        self.assertIn('false', result.stdout, "Excessive traffic not blocked")

class TestWAFSetup(unittest.TestCase):
    def test_waf_initialization(self):
        result = subprocess.run(['scala', 'security/firewall/WAFSetup.scala', 'init'], capture_output=True, text=True)
        self.assertIn('initialized', result.stdout, "WAF initialization failed")

    def test_waf_block_malicious_traffic(self):
        malicious_request = '{"url":"/login", "body":"<script>alert(\'XSS\');</script>"}'
        result = subprocess.run(['scala', 'security/firewall/WAFSetup.scala', 'analyze', malicious_request],
                                capture_output=True, text=True)
        self.assertIn('blocked', result.stdout, "WAF failed to block malicious traffic")

class TestAuditLogs(unittest.TestCase):
    def setUp(self):
        self.audit_log = AuditLog()

    def test_log_creation(self):
        event = "User login"
        self.audit_log.log_event(event)
        logs = self.audit_log.get_logs()
        self.assertIn(event, logs, "Audit log creation failed")

    def test_log_integrity(self):
        event = "Critical action"
        self.audit_log.log_event(event)
        tampered_logs = self.audit_log.get_logs()
        tampered_logs[0] = "Tampered log"
        self.assertNotEqual(self.audit_log.get_logs(), tampered_logs, "Audit log integrity check failed")

class TestTLSConfiguration(unittest.TestCase):
    def setUp(self):
        self.host = 'website.com'
        self.port = 443
        self.context = ssl.create_default_context()

    def test_tls_connection(self):
        with socket.create_connection((self.host, self.port)) as sock:
            with self.context.wrap_socket(sock, server_hostname=self.host) as ssock:
                self.assertTrue(ssock.version(), "TLS handshake failed")

    def test_tls_certificate(self):
        with socket.create_connection((self.host, self.port)) as sock:
            with self.context.wrap_socket(sock, server_hostname=self.host) as ssock:
                cert = ssock.getpeercert()
                self.assertIsNotNone(cert, "TLS certificate not received")
                self.assertIn('subject', cert, "Invalid certificate format")

class TestVulnerabilityScanning(unittest.TestCase):
    def test_sql_injection(self):
        payload = "' OR '1'='1"
        response = requests.post("https://website.com/login", data={"username": payload, "password": payload})
        self.assertNotIn("Welcome", response.text, "SQL Injection vulnerability detected")

    def test_xss_vulnerability(self):
        payload = "<script>alert('XSS');</script>"
        response = requests.post("https://website.com/comment", data={"comment": payload})
        self.assertNotIn(payload, response.text, "XSS vulnerability detected")

class TestPenetrationTesting(unittest.TestCase):
    def test_port_scan(self):
        result = subprocess.run(['nmap', '-p', '80,443', 'website.com'], capture_output=True, text=True)
        self.assertIn('80/tcp', result.stdout, "Port 80 is closed")
        self.assertIn('443/tcp', result.stdout, "Port 443 is closed")

    def test_brute_force_attack(self):
        common_passwords = ['password', '123456', 'admin']
        for password in common_passwords:
            response = requests.post("https://website.com/login", data={"username": "admin", "password": password})
            self.assertNotIn("Welcome", response.text, "Brute force vulnerability detected")

class TestFirewallProtection(unittest.TestCase):
    def test_block_ip(self):
        result = subprocess.run(['scala', 'security/firewall/WAFSetup.scala', 'block', '192.168.1.100'],
                                capture_output=True, text=True)
        self.assertIn('blocked', result.stdout, "IP blocking failed")

    def test_allow_ip(self):
        result = subprocess.run(['scala', 'security/firewall/WAFSetup.scala', 'allow', '192.168.1.100'],
                                capture_output=True, text=True)
        self.assertIn('allowed', result.stdout, "IP allowance failed")

if __name__ == '__main__':
    unittest.main()