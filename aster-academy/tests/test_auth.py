import unittest
import tempfile
import pathlib
from services.authentication import passhash, verify

class TestAuthentication(unittest.TestCase):
    def test_passhash_and_verify_success(self):
        password = "AdminSecurePassword123!"
        hashed = passhash(password)
        self.assertIn(":", hashed)
        self.assertTrue(verify(password, hashed))

    def test_verify_wrong_password(self):
        password = "AdminSecurePassword123!"
        hashed = passhash(password)
        self.assertFalse(verify("WrongPassword999!", hashed))

    def test_verify_invalid_hash_format(self):
        self.assertFalse(verify("password", "invalid_hash_string"))
        self.assertFalse(verify("password", ""))

if __name__ == "__main__":
    unittest.main()
