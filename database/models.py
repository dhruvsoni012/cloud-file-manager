from database.db import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username_hash = db.Column(db.String(128), unique=True, nullable=False)
    username_enc = db.Column(db.Text, nullable=False)  # NEW: Encrypted username
    password_hash = db.Column(db.String(128), nullable=False)
    encryption_key = db.Column(db.LargeBinary, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    email_enc = db.Column(db.Text, nullable=True)  # CHANGED: Now encrypted
    mobile_enc = db.Column(db.Text, nullable=True)  # CHANGED: Now encrypted
    storage_quota = db.Column(db.Integer, default=1073741824)  # 1GB default
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeletedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username_hash = db.Column(db.String(128), unique=True)
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    name_enc = db.Column(db.Text, nullable=False)
    name_hash = db.Column(db.String(64), index=True)
    parent_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    folder_id = db.Column(db.Integer, nullable=False)
    name_enc = db.Column(db.Text, nullable=False)
    name_hash = db.Column(db.String(64), index=True)
    path = db.Column(db.Text, nullable=False)
    size = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

class Trash(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(10), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)
    auto_delete_at = db.Column(db.DateTime, nullable=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    theme = db.Column(db.String(10), default='dark')
    view_mode = db.Column(db.String(10), default='grid')
    start_page = db.Column(db.String(50), default='/')
    trash_auto_delete_days = db.Column(db.Integer, default=30)