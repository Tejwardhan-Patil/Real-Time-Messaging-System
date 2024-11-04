from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from base64 import urlsafe_b64encode, urlsafe_b64decode
from os import urandom
import hashlib
import hmac

class MessageEncryption:
    def __init__(self, password: str):
        # Generate a secure key using the provided password
        self.salt = urandom(16)
        self.backend = default_backend()
        self.key = self.derive_key(password, self.salt)
        self.iv_length = 16  # AES block size for IV

    def derive_key(self, password: str, salt: bytes) -> bytes:
        # Derive a cryptographic key from the password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))

    def encrypt_message(self, plaintext: str) -> str:
        # Encrypts the message using AES encryption in CBC mode with padding
        iv = urandom(self.iv_length)
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        padded_data = self._pad(plaintext.encode('utf-8'))
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        # Concatenate the IV and the ciphertext for transmission
        return urlsafe_b64encode(iv + ciphertext).decode('utf-8')

    def decrypt_message(self, encrypted_message: str) -> str:
        # Decrypts the message using AES decryption in CBC mode with padding
        decoded_data = urlsafe_b64decode(encrypted_message)
        iv = decoded_data[:self.iv_length]
        ciphertext = decoded_data[self.iv_length:]

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        plaintext = self._unpad(padded_data)
        return plaintext.decode('utf-8')

    def _pad(self, data: bytes) -> bytes:
        # Pad the plaintext to a multiple of the block size
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        return padded_data

    def _unpad(self, padded_data: bytes) -> bytes:
        # Remove the padding after decryption
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        return data

    def generate_hmac(self, message: str) -> str:
        # Generate an HMAC for message integrity verification
        hmac_key = hashlib.sha256(self.key).digest()
        h = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
        return h.hexdigest()

    def verify_hmac(self, message: str, provided_hmac: str) -> bool:
        # Verify the HMAC to ensure message integrity
        generated_hmac = self.generate_hmac(message)
        return hmac.compare_digest(provided_hmac, generated_hmac)


# Utility functions for handling encrypted message files
def save_encrypted_message(filename: str, encrypted_message: str):
    with open(filename, 'w') as file:
        file.write(encrypted_message)

def load_encrypted_message(filename: str) -> str:
    with open(filename, 'r') as file:
        return file.read()


if __name__ == "__main__":
    # Usage
    password = "Password123"
    message = "This is a secure message."

    encryptor = MessageEncryption(password)

    # Encrypt the message
    encrypted_msg = encryptor.encrypt_message(message)
    print(f"Encrypted Message: {encrypted_msg}")

    # Save the encrypted message to a file
    save_encrypted_message("encrypted_message.txt", encrypted_msg)

    # Load the encrypted message from the file
    loaded_encrypted_msg = load_encrypted_message("encrypted_message.txt")

    # Decrypt the message
    decrypted_msg = encryptor.decrypt_message(loaded_encrypted_msg)
    print(f"Decrypted Message: {decrypted_msg}")

    # Generate an HMAC for the message
    hmac_value = encryptor.generate_hmac(message)
    print(f"HMAC: {hmac_value}")

    # Verify the HMAC
    is_valid_hmac = encryptor.verify_hmac(message, hmac_value)
    print(f"HMAC Verified: {is_valid_hmac}")