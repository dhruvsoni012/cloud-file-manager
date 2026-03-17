import os
from datetime import datetime, timedelta
from database.db import db
from database.models import Trash, File, Folder
from config import STORAGE_PATH

def move_to_trash(user, item_type, item_id, auto_delete_days=30):
    """Move file or folder to trash"""
    if item_type == "file":
        item = File.query.get(item_id)
        if item and item.user_id == user.id:
            item.is_deleted = True
    elif item_type == "folder":
        item = Folder.query.get(item_id)
        if item and item.user_id == user.id and item.parent_id is not None:
            item.is_deleted = True
        else:
            return False, "Cannot delete root folder"
    else:
        return False, "Invalid item type"
    
    trash = Trash(
        user_id=user.id,
        item_type=item_type,
        item_id=item_id,
        deleted_at=datetime.utcnow(),
        auto_delete_at=datetime.utcnow() + timedelta(days=auto_delete_days)
    )
    
    db.session.add(trash)
    db.session.commit()
    
    return True, "Item moved to trash"

def restore_from_trash(user, trash_id):
    """Restore item from trash"""
    t = Trash.query.get(trash_id)
    if not t or t.user_id != user.id:
        return False, "Invalid trash item"
    
    if t.item_type == "file":
        item = File.query.get(t.item_id)
        if item:
            item.is_deleted = False
    elif t.item_type == "folder":
        item = Folder.query.get(t.item_id)
        if item:
            item.is_deleted = False
    
    db.session.delete(t)
    db.session.commit()
    
    return True, "Item restored successfully"

def delete_forever(user, trash_id):
    """Permanently delete item from trash"""
    t = Trash.query.get(trash_id)
    if not t or t.user_id != user.id:
        return False, "Invalid trash item"
    
    if t.item_type == "file":
        item = File.query.get(t.item_id)
        if item:
            # Delete physical file
            if os.path.exists(item.path):
                os.remove(item.path)
            db.session.delete(item)
    elif t.item_type == "folder":
        item = Folder.query.get(t.item_id)
        if item:
            db.session.delete(item)
    
    db.session.delete(t)
    db.session.commit()
    
    return True, "Item permanently deleted"

def empty_trash(user):
    """Empty all trash items for user"""
    trash_items = Trash.query.filter_by(user_id=user.id).all()
    
    for t in trash_items:
        delete_forever(user, t.id)
    
    return True, "Trash emptied successfully"