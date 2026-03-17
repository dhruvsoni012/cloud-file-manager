from cryptography.fernet import Fernet
import os

# Master key for encrypting user keys
MASTER_KEY = os.environ.get("CLOUD_MASTER_KEY")

if not MASTER_KEY:
    MASTER_KEY = Fernet.generate_key()
    print(f"\n{'='*70}")
    print(f"⚠️  WARNING: No CLOUD_MASTER_KEY environment variable found!")
    print(f"{'='*70}")
    print(f"Generated temporary master key (will change on restart):")
    print(f"\n{MASTER_KEY.decode()}\n")
    print(f"To persist this key, add to your environment:")
    print(f"export CLOUD_MASTER_KEY=\"{MASTER_KEY.decode()}\"")
    print(f"{'='*70}\n")
else:
    MASTER_KEY = MASTER_KEY.encode() if isinstance(MASTER_KEY, str) else MASTER_KEY

def generate_user_key():
    """Generate a new encryption key for a user"""
    return Fernet.generate_key()

def encrypt_key(user_key):
    """Encrypt user key with master key"""
    f = Fernet(MASTER_KEY)
    return f.encrypt(user_key)

def decrypt_key(enc_key):
    """Decrypt user key with master key"""
    f = Fernet(MASTER_KEY)
    return f.decrypt(enc_key)