from database.db import db
from database.models import User, DeletedUser
from crypto.key_manager import generate_user_key, encrypt_key, decrypt_key, MASTER_KEY
from crypto.indexer import hash_username
from crypto.text import encrypt_text, decrypt_text
from cryptography.fernet import Fernet
import bcrypt

def encrypt_with_master_key(text):
    """Encrypt text with master key (for admin-viewable data)"""
    if not text:
        return None
    f = Fernet(MASTER_KEY)
    return f.encrypt(text.encode()).decode()

def decrypt_with_master_key(encrypted_text):
    """Decrypt text with master key"""
    if not encrypted_text:
        return None
    f = Fernet(MASTER_KEY)
    return f.decrypt(encrypted_text.encode()).decode()

def create_user(username, password, email=None, mobile=None, is_admin=False):
    """Create a new user account with encrypted personal data"""
    h = hash_username(username)
    
    # Block reused usernames forever
    if User.query.filter_by(username_hash=h).first():
        return False, "Username already exists"
    
    if DeletedUser.query.filter_by(username_hash=h).first():
        return False, "Username permanently blocked"
    
    # Hash password with bcrypt
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    # Generate per-user encryption key
    raw_key = generate_user_key()
    enc_key = encrypt_key(raw_key)
    
    # Encrypt username, email, and mobile with master key (admin can decrypt)
    username_encrypted = encrypt_with_master_key(username)
    email_encrypted = encrypt_with_master_key(email) if email else None
    mobile_encrypted = encrypt_with_master_key(mobile) if mobile else None
    
    user = User(
        username_hash=h,
        username_enc=username_encrypted,
        password_hash=pw,
        encryption_key=enc_key,
        email_enc=email_encrypted,
        mobile_enc=mobile_encrypted,
        is_admin=is_admin
    )
    
    db.session.add(user)
    db.session.commit()
    
    return True, "User created successfully"

def verify_user(username, password):
    """Verify user credentials"""
    h = hash_username(username)
    
    user = User.query.filter_by(username_hash=h).first()
    if not user:
        return None
    
    if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return user
    
    return None

def change_password(user, old_password, new_password):
    """Change user password"""
    if not bcrypt.checkpw(old_password.encode(), user.password_hash.encode()):
        return False, "Old password is incorrect"
    
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    user.password_hash = new_hash
    db.session.commit()
    
    return True, "Password changed successfully"

def get_decrypted_username(user):
    """Get decrypted username"""
    return decrypt_with_master_key(user.username_enc)

def get_decrypted_email(user):
    """Get decrypted email"""
    return decrypt_with_master_key(user.email_enc) if user.email_enc else None

def get_decrypted_mobile(user):
    """Get decrypted mobile"""
    return decrypt_with_master_key(user.mobile_enc) if user.mobile_enc else None