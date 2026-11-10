from __future__ import annotations
import hashlib
import secrets

def passhash(password, salt=None):
    salt=salt or secrets.token_bytes(16)
    return salt.hex()+':'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt,240000).hex()

def verify(password, encoded):
    try:
        salt,digest=encoded.split(':',1); return secrets.compare_digest(passhash(password,bytes.fromhex(salt)).split(':')[1],digest)
    except Exception: return False
