import os
import uuid
from database.db import db
from database.models import File, Folder
from crypto.encrypt import encrypt_bytes
from crypto.decrypt import decrypt_bytes
from crypto.text import encrypt_text, decrypt_text
from crypto.indexer import hash_name
from crypto.key_manager import decrypt_key
from config import STORAGE_PATH

def get_user_key(user):
    """Get decrypted user encryption key"""
    return decrypt_key(user.encryption_key)

def save_file(user, folder, file_obj):
    """Save and encrypt a file"""
    key = get_user_key(user)
    
    # Read file data
    raw_data = file_obj.read()
    
    # Encrypt file data
    enc_data = encrypt_bytes(raw_data, key)
    
    # Generate unique storage name
    storage_name = str(uuid.uuid4())
    file_path = os.path.join(STORAGE_PATH, storage_name)
    
    # Write encrypted data to disk
    with open(file_path, "wb") as f:
        f.write(enc_data)
    
    # Encrypt filename
    enc_name = encrypt_text(file_obj.filename, key)
    name_hash_val = hash_name(file_obj.filename)
    
    # Create database entry
    file_row = File(
        user_id=user.id,
        folder_id=folder.id,
        name_enc=enc_name,
        name_hash=name_hash_val,
        path=file_path,
        size=len(raw_data)
    )
    
    db.session.add(file_row)
    db.session.commit()
    
    return file_row

def load_file(user, file_row):
    """Load and decrypt a file"""
    key = get_user_key(user)
    
    with open(file_row.path, "rb") as f:
        enc_data = f.read()
    
    return decrypt_bytes(enc_data, key)

def get_filename(user, file_row):
    """Get decrypted filename"""
    key = get_user_key(user)
    return decrypt_text(file_row.name_enc, key)

def rename_file(user, file_id, new_name):
    """Rename a file"""
    file_row = File.query.get(file_id)
    if not file_row or file_row.user_id != user.id:
        return False, "Invalid file"
    
    key = get_user_key(user)
    file_row.name_enc = encrypt_text(new_name, key)
    file_row.name_hash = hash_name(new_name)
    
    db.session.commit()
    return True, "File renamed successfully"

def get_storage_usage(user):
    """Calculate total storage used by user"""
    files = File.query.filter_by(user_id=user.id, is_deleted=False).all()
    return sum(f.size for f in files)