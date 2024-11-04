import unittest
import subprocess
from unittest.mock import patch

class NotificationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Paths to the compiled services for notifications
        cls.fcm_service_path = "/notifications/push_notifications/FCMService.jar"  # Java JAR for FCM
        cls.apns_service_path = "/notifications/push_notifications/APNSService"    # Go binary for APNS
        cls.in_app_service_path = "/notifications/InAppNotifications"  # Scala binary for In-App

    def run_subprocess(self, command):
        """Helper function to run a subprocess command"""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.output.strip()}"

    def test_fcm_send_notification(self):
        """Test sending a notification via FCM (Java)"""
        command = ["java", "-jar", self.fcm_service_path, "device_token_123", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Success", result)

    def test_fcm_failed_notification(self):
        """Test handling failure of FCM notification (Java)"""
        command = ["java", "-jar", self.fcm_service_path, "invalid_token", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_apns_send_notification(self):
        """Test sending a notification via APNS (Go)"""
        command = [self.apns_service_path, "device_token_abc", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Success", result)

    def test_apns_failed_notification(self):
        """Test handling failure of APNS notification (Go)"""
        command = [self.apns_service_path, "invalid_token", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_in_app_notification(self):
        """Test sending an in-app notification (Scala)"""
        command = [self.in_app_service_path, "user_123", "New message received", "Test Message Content"]
        result = self.run_subprocess(command)
        self.assertIn("Success", result)

    def test_in_app_failed_notification(self):
        """Test handling failure of in-app notification (Scala)"""
        command = [self.in_app_service_path, "non_existent_user", "New message received", "Test Message Content"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_web_push_send_notification(self):
        """Test sending a web push notification (Python)"""
        command = ["python3", "WebPushService.py", "subscription_123", "New Update", "Message body"]
        result = self.run_subprocess(command)
        self.assertIn("Success", result)

    def test_web_push_failed_notification(self):
        """Test handling failure of web push notification (Python)"""
        command = ["python3", "WebPushService.py", "invalid_subscription", "New Update", "Message body"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_fcm_notification_invalid_token(self):
        """Test FCM notification with invalid device token (Java)"""
        command = ["java", "-jar", self.fcm_service_path, "invalid_token", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_apns_notification_invalid_token(self):
        """Test APNS notification with invalid device token (Go)"""
        command = [self.apns_service_path, "invalid_token", "Test Title", "Test Message"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_in_app_notification_user_not_found(self):
        """Test in-app notification when user is not found (Scala)"""
        command = [self.in_app_service_path, "non_existent_user", "Notification", "Content"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

    def test_web_push_invalid_subscription(self):
        """Test web push notification with invalid subscription (Python)"""
        command = ["python3", "WebPushService.py", "invalid_subscription", "New Update", "Message body"]
        result = self.run_subprocess(command)
        self.assertIn("Error", result)

if __name__ == '__main__':
    unittest.main()