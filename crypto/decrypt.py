from cryptography.fernet import Fernet

def decrypt_bytes(data, key):
    """Decrypt file bytes"""
    return Fernet(key).decrypt(data)