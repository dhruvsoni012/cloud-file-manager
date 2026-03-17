from database.db import db
from database.models import Folder
from crypto.text import encrypt_text, decrypt_text
from crypto.indexer import hash_name
from crypto.key_manager import decrypt_key

def get_user_key(user):
    """Get decrypted user encryption key"""
    return decrypt_key(user.encryption_key)

def get_or_create_root(user):
    """Get or create root folder for user"""
    root = Folder.query.filter_by(
        user_id=user.id, 
        parent_id=None, 
        is_deleted=False
    ).first()
    
    if not root:
        key = get_user_key(user)
        root = Folder(
            user_id=user.id,
            name_enc=encrypt_text("My Drive", key),
            name_hash=hash_name("My Drive"),
            parent_id=None
        )
        db.session.add(root)
        db.session.commit()
    
    return root

def create_folder(user, name, parent_id):
    """Create a new folder"""
    parent = Folder.query.get(parent_id)
    if not parent or parent.user_id != user.id:
        return None, "Invalid parent folder"
    
    key = get_user_key(user)
    
    folder = Folder(
        user_id=user.id,
        name_enc=encrypt_text(name, key),
        name_hash=hash_name(name),
        parent_id=parent.id
    )
    
    db.session.add(folder)
    db.session.commit()
    
    return folder, "Folder created successfully"

def rename_folder(user, folder_id, new_name):
    """Rename a folder"""
    folder = Folder.query.get(folder_id)
    if not folder or folder.user_id != user.id or folder.parent_id is None:
        return False, "Invalid folder or cannot rename root"
    
    key = get_user_key(user)
    folder.name_enc = encrypt_text(new_name, key)
    folder.name_hash = hash_name(new_name)
    
    db.session.commit()
    return True, "Folder renamed successfully"

def get_folder_path(user, folder):
    """Get breadcrumb path for a folder"""
    key = get_user_key(user)
    path = []
    
    current = folder
    while current:
        path.insert(0, {
            'id': current.id,
            'name': decrypt_text(current.name_enc, key)
        })
        current = Folder.query.get(current.parent_id) if current.parent_id else None
    
    return path