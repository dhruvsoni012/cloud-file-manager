from cryptography.fernet import Fernet

def encrypt_bytes(data, key):
    """Encrypt file bytes"""
    return Fernet(key).encrypt(data)