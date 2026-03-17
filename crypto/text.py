from cryptography.fernet import Fernet

def encrypt_text(text, key):
    """Encrypt text (filenames, folder names)"""
    return Fernet(key).encrypt(text.encode()).decode()

def decrypt_text(encrypted_text, key):
    """Decrypt text"""
    return Fernet(key).decrypt(encrypted_text.encode()).decode()