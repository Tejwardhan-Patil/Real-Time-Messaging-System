import json
import logging
from typing import Dict, Optional
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebPushService:
    def __init__(self, vapid_private_key: str, vapid_public_key: str, vapid_email: str):
        self.vapid_private_key = vapid_private_key
        self.vapid_public_key = vapid_public_key
        self.vapid_email = vapid_email

    def _generate_vapid_keys(self):
        """
        Generates a new pair of VAPID keys (private and public).
        """
        logger.info("Generating new VAPID keys.")
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode('utf-8')

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode('utf-8')

        return private_key_pem, public_key_pem

    def send_notification(self, subscription_info: Dict, payload: Dict, ttl: int = 60):
        """
        Sends a push notification to a client.
        
        :param subscription_info: The subscription details including the endpoint, p256dh key, and auth key.
        :param payload: The notification payload.
        :param ttl: Time to live in seconds.
        """
        logger.info("Preparing to send push notification.")
        endpoint = subscription_info.get('endpoint')
        keys = subscription_info.get('keys')
        if not endpoint or not keys:
            logger.error("Invalid subscription information.")
            raise ValueError("Invalid subscription information.")

        try:
            response = webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                },
                ttl=ttl
            )
            logger.info(f"Notification sent successfully: {response.status_code}")
        except WebPushException as ex:
            logger.error(f"Failed to send notification: {ex}")
            if ex.response and ex.response.json():
                logger.error(f"WebPush response details: {ex.response.json()}")
            raise

    def subscribe(self, subscription_data: Dict, db) -> bool:
        """
        Stores or validates a subscription. Implement the storage of subscription in persistence layer.

        :param subscription_data: The subscription data to store.
        :return: True if subscription was stored/updated successfully, False otherwise.
        """
        logger.info("Subscribing new user.")
        if not subscription_data:
            logger.error("Empty subscription data.")
            return False

        try:
            result = db.save_subscription(subscription_data)  

            if result:  
                logger.info("Subscription stored successfully.")
                return True
            else:
                logger.error("Failed to store subscription.")
                return False
        except Exception as e:
            logger.error(f"An error occurred while storing subscription: {e}")
            return False

    def unsubscribe(self, endpoint: str, db) -> bool:
        """
        Removes a subscription from the system.

        :param endpoint: The subscription endpoint to remove.
        :return: True if unsubscribed successfully, False otherwise.
        """
        logger.info(f"Unsubscribing user with endpoint {endpoint}.")
        if not endpoint:
            logger.error("Endpoint is required to unsubscribe.")
            return False

        try:
            result = db.delete_subscription(endpoint) 

            if result:  
                logger.info(f"Subscription for endpoint {endpoint} removed successfully.")
                return True
            else:
                logger.error(f"Failed to remove subscription for endpoint {endpoint}.")
                return False
        except Exception as e:
            logger.error(f"An error occurred while removing subscription for {endpoint}: {e}")
            return False

    def _validate_subscription(self, subscription_info: Dict) -> bool:
        """
        Validates the structure of the subscription info.

        :param subscription_info: The subscription details to validate.
        :return: True if valid, False otherwise.
        """
        if not subscription_info.get('endpoint'):
            logger.error("Subscription missing endpoint.")
            return False
        if 'keys' not in subscription_info or 'p256dh' not in subscription_info['keys'] or 'auth' not in subscription_info['keys']:
            logger.error("Subscription keys missing.")
            return False
        return True

    def handle_incoming_subscription(self, subscription_info: Dict, action: str):
        """
        Handles subscription actions (subscribe/unsubscribe).

        :param subscription_info: The subscription information.
        :param action: The action to perform ('subscribe' or 'unsubscribe').
        """
        if action == 'subscribe':
            if not self._validate_subscription(subscription_info):
                logger.error("Invalid subscription format.")
                return False
            return self.subscribe(subscription_info)
        elif action == 'unsubscribe':
            return self.unsubscribe(subscription_info.get('endpoint'))
        else:
            logger.error(f"Unknown action: {action}")
            return False

    def get_vapid_public_key(self) -> str:
        """
        Returns the VAPID public key for clients to use during subscription.

        :return: VAPID public key in PEM format.
        """
        logger.info("Returning VAPID public key.")
        return self.vapid_public_key

    def send_bulk_notifications(self, subscriptions: Dict[str, Dict], payload: Dict, ttl: int = 60):
        """
        Sends notifications to multiple subscribers.

        :param subscriptions: A dictionary where keys are user identifiers and values are subscription details.
        :param payload: The notification payload.
        :param ttl: Time to live in seconds.
        """
        logger.info(f"Sending bulk notifications to {len(subscriptions)} users.")
        for user_id, subscription_info in subscriptions.items():
            try:
                self.send_notification(subscription_info, payload, ttl)
            except Exception as ex:
                logger.error(f"Failed to send notification to user {user_id}: {ex}")

    def renew_vapid_keys(self):
        """
        Renews VAPID keys and updates the service with new keys.
        """
        logger.info("Renewing VAPID keys.")
        self.vapid_private_key, self.vapid_public_key = self._generate_vapid_keys()

# Usage

if __name__ == '__main__':
    # Pre-generated VAPID keys for the server
    private_key = "<VAPID_PRIVATE_KEY>"
    public_key = "<VAPID_PUBLIC_KEY>"
    email = "contact@website.com"

    web_push_service = WebPushService(private_key, public_key, email)

    # Payload and subscription info
    subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/eBQ...",
        "keys": {
            "p256dh": "BNc...",
            "auth": "aBc..."
        }
    }

    payload = {
        "title": "New Message",
        "body": "You have a new message.",
        "icon": "/icon.png"
    }

    web_push_service.send_notification(subscription, payload)