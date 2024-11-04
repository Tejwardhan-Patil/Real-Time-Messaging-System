import unittest
import subprocess
from auth.JWTAuth import JWTAuth
from auth.Permissions import Permissions
import datetime
import jwt
import json

class AuthTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.jwt_auth = JWTAuth()
        cls.permissions = Permissions()

    def test_jwt_token_creation(self):
        user_id = 123
        roles = ['admin', 'user']
        token = self.jwt_auth.create_token(user_id, roles)
        self.assertIsNotNone(token)
        decoded_token = jwt.decode(token, self.jwt_auth.secret, algorithms=["HS256"])
        self.assertEqual(decoded_token['user_id'], user_id)
        self.assertEqual(decoded_token['roles'], roles)

    def test_jwt_token_expiration(self):
        user_id = 123
        roles = ['admin', 'user']
        expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
        token = self.jwt_auth.create_token(user_id, roles, expiration)
        self.assertIsNotNone(token)
        decoded_token = jwt.decode(token, self.jwt_auth.secret, algorithms=["HS256"])
        self.assertEqual(decoded_token['user_id'], user_id)
        self.assertEqual(decoded_token['roles'], roles)
        self.assertTrue('exp' in decoded_token)

    def test_jwt_token_invalid(self):
        invalid_token = "invalid.token.string"
        with self.assertRaises(jwt.InvalidTokenError):
            self.jwt_auth.decode_token(invalid_token)

    def test_jwt_token_expired(self):
        user_id = 123
        roles = ['admin']
        expiration = datetime.datetime.utcnow() - datetime.timedelta(seconds=1)
        token = self.jwt_auth.create_token(user_id, roles, expiration)
        with self.assertRaises(jwt.ExpiredSignatureError):
            self.jwt_auth.decode_token(token)

    def test_jwt_token_role_based_access(self):
        user_id = 123
        roles = ['admin']
        token = self.jwt_auth.create_token(user_id, roles)
        decoded_token = self.jwt_auth.decode_token(token)
        self.assertTrue(self.permissions.has_role(decoded_token, 'admin'))
        self.assertFalse(self.permissions.has_role(decoded_token, 'user'))

    def test_permissions_user_role(self):
        user_roles = ['user']
        result = self.permissions.has_role({'roles': user_roles}, 'user')
        self.assertTrue(result)

    def test_permissions_admin_role(self):
        user_roles = ['user', 'admin']
        result = self.permissions.has_role({'roles': user_roles}, 'admin')
        self.assertTrue(result)

    def test_permissions_no_role(self):
        user_roles = ['user']
        result = self.permissions.has_role({'roles': user_roles}, 'admin')
        self.assertFalse(result)

    def test_google_oauth_token_validation(self):
        token = "google_token"
        result = subprocess.run(['java', '-cp', 'auth/oauth2/GoogleOAuth', 'GoogleOAuth', token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIsNotNone(user_info)
        self.assertIn('email', user_info)

    def test_google_oauth_invalid_token(self):
        invalid_token = "invalid_token"
        result = subprocess.run(['java', '-cp', 'auth/oauth2/GoogleOAuth', 'GoogleOAuth', invalid_token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIsNone(user_info)

    def test_facebook_oauth_token_validation(self):
        token = "facebook_token"
        result = subprocess.run(['scala', 'auth/oauth2/FacebookOAuth', token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIsNotNone(user_info)
        self.assertIn('email', user_info)

    def test_facebook_oauth_invalid_token(self):
        invalid_token = "invalid_facebook_token"
        result = subprocess.run(['scala', 'auth/oauth2/FacebookOAuth', invalid_token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIsNone(user_info)

    def test_jwt_role_access_admin(self):
        user_id = 100
        roles = ['admin']
        token = self.jwt_auth.create_token(user_id, roles)
        decoded_token = self.jwt_auth.decode_token(token)
        self.assertTrue(self.permissions.has_role(decoded_token, 'admin'))

    def test_jwt_role_access_no_access(self):
        user_id = 100
        roles = ['user']
        token = self.jwt_auth.create_token(user_id, roles)
        decoded_token = self.jwt_auth.decode_token(token)
        self.assertFalse(self.permissions.has_role(decoded_token, 'admin'))

    def test_jwt_creation_with_long_expiration(self):
        user_id = 123
        roles = ['user']
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        token = self.jwt_auth.create_token(user_id, roles, expiration)
        decoded_token = self.jwt_auth.decode_token(token)
        self.assertEqual(decoded_token['user_id'], user_id)
        self.assertEqual(decoded_token['roles'], roles)

    def test_jwt_invalid_signature(self):
        user_id = 123
        roles = ['user']
        token = self.jwt_auth.create_token(user_id, roles)
        invalid_token = token + "invalid"
        with self.assertRaises(jwt.InvalidSignatureError):
            self.jwt_auth.decode_token(invalid_token)

    def test_jwt_missing_user_role(self):
        user_id = 123
        roles = []
        token = self.jwt_auth.create_token(user_id, roles)
        decoded_token = self.jwt_auth.decode_token(token)
        self.assertFalse(self.permissions.has_role(decoded_token, 'admin'))
        self.assertFalse(self.permissions.has_role(decoded_token, 'user'))

    def test_oauth_user_roles(self):
        google_token = "google_token"
        result = subprocess.run(['java', '-cp', 'auth/oauth2/GoogleOAuth', 'GoogleOAuth', google_token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIn('email', user_info)
        self.assertIn('roles', user_info)

    def test_oauth_invalid_user_roles(self):
        facebook_token = "invalid_facebook_token"
        result = subprocess.run(['scala', 'auth/oauth2/FacebookOAuth', facebook_token], capture_output=True, text=True)
        user_info = json.loads(result.stdout)
        self.assertIsNone(user_info)

    def test_jwt_invalid_structure(self):
        invalid_token = "header.payload"
        with self.assertRaises(jwt.DecodeError):
            self.jwt_auth.decode_token(invalid_token)

if __name__ == '__main__':
    unittest.main()