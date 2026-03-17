from flask import Flask, render_template, request, redirect, session, abort, jsonify, send_file
from database.db import db
from database.models import User, File, Folder, Trash, AuditLog, UserSettings, DeletedUser
from core.auth import create_user, verify_user, change_password
from core.files import save_file, load_file, get_filename, rename_file, get_storage_usage, get_user_key
from core.folders import get_or_create_root, create_folder, rename_folder, get_folder_path
from core.trash import move_to_trash, restore_from_trash, delete_forever, empty_trash
from core.search import search_items
from core.audit import log_event, get_user_logs, get_all_logs
from crypto.text import decrypt_text
from crypto.key_manager import decrypt_key
from crypto.decrypt import decrypt_bytes
from crypto.encrypt import encrypt_bytes

from config import DATABASE_PATH, SECRET_KEY, STORAGE_PATH
from functools import wraps
from datetime import datetime, timedelta
from io import BytesIO
import os
import uuid
from core.auth import create_user, verify_user, change_password, get_decrypted_username, get_decrypted_email, get_decrypted_mobile

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max upload

db.init_app(app)

with app.app_context():
    db.create_all()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def current_user():
    """Get current logged-in user"""
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

def get_user_settings(user):
    """Get or create user settings"""
    settings = UserSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()
    return settings

def format_size(bytes_size):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"

# ============================================================================
# AUTH ROUTES
# ============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            return render_template("login.html", error="Username and password required")
        
        user = verify_user(username, password)
        
        if not user:
            log_event(None, "failed_login", f"Username: {username}", request.remote_addr)
            return render_template("login.html", error="Invalid credentials")
        
        session["user_id"] = user.id
        session["is_admin"] = user.is_admin
        
        log_event(user, "login", "", request.remote_addr)
        
        settings = get_user_settings(user)
        return redirect(settings.start_page)
    
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        
        if not username or not password:
            return render_template("signup.html", error="Username and password required")
        
        if len(password) < 8:
            return render_template("signup.html", error="Password must be at least 8 characters")
        
        if not email and not mobile:
            return render_template("signup.html", error="Email or mobile number required")
        
        ok, msg = create_user(username, password, email, mobile)
        
        if not ok:
            return render_template("signup.html", error=msg)
        
        # Get the created user and create root folder
        user = verify_user(username, password)
        if user:
            get_or_create_root(user)
            log_event(user, "signup", "", request.remote_addr)
        
        return redirect("/login")
    
    return render_template("signup.html")

@app.route("/logout")
def logout():
    user = current_user()
    if user:
        log_event(user, "logout")
    session.clear()
    return redirect("/login")

# ============================================================================
# HOME & DASHBOARD
# ============================================================================

@app.route("/")
@login_required
def home():
    user = current_user()
    settings = get_user_settings(user)
    
    total_files = File.query.filter_by(user_id=user.id, is_deleted=False).count()
    total_folders = Folder.query.filter_by(user_id=user.id, is_deleted=False).count() - 1
    
    recent_files = File.query.filter_by(user_id=user.id, is_deleted=False)\
        .order_by(File.uploaded_at.desc()).limit(5).all()
    
    key = decrypt_key(user.encryption_key)
    recent_files_data = []
    
    for f in recent_files:
        folder = Folder.query.get(f.folder_id)
        recent_files_data.append({
            'id': f.id,
            'name': decrypt_text(f.name_enc, key),
            'folder': decrypt_text(folder.name_enc, key) if folder else 'Unknown',
            'size': format_size(f.size),
            'uploaded': f.uploaded_at.strftime('%Y-%m-%d %H:%M')
        })
    
    used = get_storage_usage(user)
    quota = user.storage_quota
    percent = int((used / quota) * 100) if quota > 0 else 0
    
    return render_template(
        "home.html",
        total_files=total_files,
        total_folders=total_folders,
        recent_files=recent_files_data,
        storage_used=format_size(used),
        storage_quota=format_size(quota),
        storage_percent=percent,
        theme=settings.theme
    )

# ============================================================================
# DRIVE & FILE OPERATIONS
# ============================================================================

@app.route("/drive")
@app.route("/drive/<int:folder_id>")
@login_required
def drive(folder_id=None):
    user = current_user()
    settings = get_user_settings(user)
    key = decrypt_key(user.encryption_key)
    
    if folder_id:
        current_folder = Folder.query.get(folder_id)
        if not current_folder or current_folder.user_id != user.id:
            abort(404)
    else:
        current_folder = get_or_create_root(user)
    
    folders = Folder.query.filter_by(
        user_id=user.id,
        parent_id=current_folder.id,
        is_deleted=False
    ).all()
    
    files = File.query.filter_by(
        user_id=user.id,
        folder_id=current_folder.id,
        is_deleted=False
    ).all()
    
    folders_data = [{
        'id': f.id,
        'name': decrypt_text(f.name_enc, key),
        'created': f.created_at.strftime('%Y-%m-%d')
    } for f in folders]
    
    files_data = [{
        'id': f.id,
        'name': decrypt_text(f.name_enc, key),
        'size': format_size(f.size),
        'uploaded': f.uploaded_at.strftime('%Y-%m-%d %H:%M')
    } for f in files]
    
    breadcrumb = get_folder_path(user, current_folder)
    
    return render_template(
        "drive.html",
        folders=folders_data,
        files=files_data,
        current_folder_id=current_folder.id,
        breadcrumb=breadcrumb,
        view_mode=settings.view_mode,
        theme=settings.theme
    )

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    user = current_user()
    folder_id = request.form.get("folder_id")
    
    folder = Folder.query.get(folder_id)
    if not folder or folder.user_id != user.id:
        return jsonify({"success": False, "error": "Invalid folder"}), 400
    
    files = request.files.getlist("files")
    if not files:
        return jsonify({"success": False, "error": "No files uploaded"}), 400
    
    uploaded_count = 0
    key = get_user_key(user)
    
    # Get file paths for folder structure preservation
    file_paths = request.form.getlist("file_paths")
    
    for idx, file_obj in enumerate(files):
        if file_obj.filename:
            # Check if we have a path (for folder uploads)
            if file_paths and idx < len(file_paths):
                file_path = file_paths[idx]
                # Create folder structure
                target_folder = create_folder_structure(user, folder, file_path, key)
            else:
                target_folder = folder
            
            # Check quota
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            file_obj.seek(0)
            
            used = get_storage_usage(user)
            if used + file_size > user.storage_quota:
                return jsonify({"success": False, "error": "Storage quota exceeded"}), 400
            
            save_file(user, target_folder, file_obj)
            uploaded_count += 1
    
    log_event(user, "upload", f"Uploaded {uploaded_count} files")
    
    return jsonify({"success": True, "count": uploaded_count})

def create_folder_structure(user, base_folder, file_path, key):
    """Create folder structure for uploaded folders"""
    from crypto.text import encrypt_text
    from crypto.indexer import hash_name
    
    # Split path into parts
    parts = file_path.split('/')
    
    # Remove filename (last part)
    folder_parts = parts[:-1]
    
    if not folder_parts:
        return base_folder
    
    current_folder = base_folder
    
    for folder_name in folder_parts:
        # Check if folder exists
        existing = Folder.query.filter_by(
            user_id=user.id,
            parent_id=current_folder.id,
            name_hash=hash_name(folder_name),
            is_deleted=False
        ).first()
        
        if existing:
            current_folder = existing
        else:
            # Create new folder
            new_folder = Folder(
                user_id=user.id,
                name_enc=encrypt_text(folder_name, key),
                name_hash=hash_name(folder_name),
                parent_id=current_folder.id
            )
            db.session.add(new_folder)
            db.session.flush()  # Get the ID
            current_folder = new_folder
    
    return current_folder

@app.route("/download/<int:file_id>")
@login_required
def download(file_id):
    user = current_user()
    file_row = File.query.get(file_id)
    
    if not file_row or file_row.user_id != user.id or file_row.is_deleted:
        abort(404)
    
    dec_data = load_file(user, file_row)
    filename = get_filename(user, file_row)
    
    log_event(user, "download", f"File: {filename}")
    
    return send_file(
        BytesIO(dec_data),
        download_name=filename,
        as_attachment=True
    )

@app.route("/new-folder", methods=["POST"])
@login_required
def new_folder():
    user = current_user()
    name = request.form.get("name", "").strip()
    parent_id = request.form.get("parent_id")
    
    if not name:
        return jsonify({"success": False, "error": "Folder name required"}), 400
    
    if not parent_id:
        parent = get_or_create_root(user)
        parent_id = parent.id
    
    folder, msg = create_folder(user, name, parent_id)
    
    if not folder:
        return jsonify({"success": False, "error": msg}), 400
    
    log_event(user, "create_folder", f"Folder: {name}")
    
    return jsonify({"success": True})

@app.route("/rename", methods=["POST"])
@login_required
def rename():
    user = current_user()
    item_type = request.form.get("type")
    item_id = request.form.get("id")
    new_name = request.form.get("name", "").strip()
    
    if not new_name:
        return jsonify({"success": False, "error": "Name required"}), 400
    
    if item_type == "file":
        ok, msg = rename_file(user, item_id, new_name)
    elif item_type == "folder":
        ok, msg = rename_folder(user, item_id, new_name)
    else:
        return jsonify({"success": False, "error": "Invalid type"}), 400
    
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    
    log_event(user, "rename", f"{item_type} renamed to: {new_name}")
    
    return jsonify({"success": True})

@app.route("/delete", methods=["POST"])
@login_required
def delete_item():
    user = current_user()
    settings = get_user_settings(user)
    item_type = request.form.get("type")
    item_id = request.form.get("id")
    
    ok, msg = move_to_trash(user, item_type, item_id, settings.trash_auto_delete_days)
    
    if not ok:
        return jsonify({"success": False, "error": msg}), 400
    
    log_event(user, "delete", f"{item_type} ID: {item_id}")
    
    return jsonify({"success": True})

# ============================================================================
# TRASH MANAGEMENT
# ============================================================================

@app.route("/trash")
@login_required
def trash():
    user = current_user()
    settings = get_user_settings(user)
    key = decrypt_key(user.encryption_key)
    
    trash_items = Trash.query.filter_by(user_id=user.id).all()
    
    items_data = []
    for t in trash_items:
        if t.item_type == "file":
            item = File.query.get(t.item_id)
            if item:
                items_data.append({
                    'trash_id': t.id,
                    'type': 'file',
                    'name': decrypt_text(item.name_enc, key),
                    'size': format_size(item.size),
                    'deleted_at': t.deleted_at.strftime('%Y-%m-%d %H:%M'),
                    'auto_delete_at': t.auto_delete_at.strftime('%Y-%m-%d')
                })
        elif t.item_type == "folder":
            item = Folder.query.get(t.item_id)
            if item:
                items_data.append({
                    'trash_id': t.id,
                    'type': 'folder',
                    'name': decrypt_text(item.name_enc, key),
                    'size': '-',
                    'deleted_at': t.deleted_at.strftime('%Y-%m-%d %H:%M'),
                    'auto_delete_at': t.auto_delete_at.strftime('%Y-%m-%d')
                })
    
    return render_template("trash.html", items=items_data, theme=settings.theme)

@app.route("/trash/restore/<int:trash_id>", methods=["POST"])
@login_required
def restore_trash(trash_id):
    user = current_user()
    ok, msg = restore_from_trash(user, trash_id)
    
    if not ok:
        return jsonify({"success": False, "error": msg}), 403
    
    log_event(user, "restore", f"Trash ID: {trash_id}")
    
    return redirect("/trash")

@app.route("/trash/delete/<int:trash_id>", methods=["POST"])
@login_required
def delete_trash(trash_id):
    user = current_user()
    ok, msg = delete_forever(user, trash_id)
    
    if not ok:
        return jsonify({"success": False, "error": msg}), 403
    
    log_event(user, "delete_forever", f"Trash ID: {trash_id}")
    
    return redirect("/trash")

@app.route("/trash/empty", methods=["POST"])
@login_required
def empty_trash_route():
    user = current_user()
    ok, msg = empty_trash(user)
    
    log_event(user, "empty_trash")
    
    return redirect("/trash")

# ============================================================================
# SEARCH
# ============================================================================

@app.route("/search")
@login_required
def search():
    user = current_user()
    settings = get_user_settings(user)
    query = request.args.get("q", "").strip()
    
    results = search_items(user, query)
    
    log_event(user, "search", f"Query: {query}")
    
    return render_template("search_results.html", results=results, query=query, theme=settings.theme)

# ============================================================================
# PROFILE & STORAGE
# ============================================================================

@app.route("/profile")
@login_required
def profile():
    user = current_user()
    settings = get_user_settings(user)
    
    used = get_storage_usage(user)
    quota = user.storage_quota
    percent = int((used / quota) * 100) if quota > 0 else 0
    
    # Decrypt personal information
    username = get_decrypted_username(user)
    email = get_decrypted_email(user)
    mobile = get_decrypted_mobile(user)
    
    return render_template(
        "profile.html",
        user=user,
        username=username,
        email=email,
        mobile=mobile,
        used=format_size(used),
        quota=format_size(quota),
        percent=percent,
        theme=settings.theme
    )

@app.route("/change-password", methods=["POST"])
@login_required
def change_password_route():
    user = current_user()
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    
    ok, msg = change_password(user, old_password, new_password)
    
    if not ok:
        return render_template("profile.html", user=user, error=msg, theme=get_user_settings(user).theme)
    
    log_event(user, "change_password")
    
    return render_template("profile.html", user=user, success=msg, theme=get_user_settings(user).theme)

@app.route("/storage")
@login_required
def storage():
    user = current_user()
    settings = get_user_settings(user)
    key = decrypt_key(user.encryption_key)
    
    used = get_storage_usage(user)
    quota = user.storage_quota
    percent = int((used / quota) * 100) if quota > 0 else 0
    
    files = File.query.filter_by(user_id=user.id, is_deleted=False).all()
    
    largest = sorted(files, key=lambda x: x.size, reverse=True)[:10]
    largest_data = [{
        'id': f.id,
        'name': decrypt_text(f.name_enc, key),
        'size': format_size(f.size),
        'folder_id': f.folder_id
    } for f in largest]
    
    return render_template(
        "storage.html",
        used=format_size(used),
        quota=format_size(quota),
        percent=percent,
        largest=largest_data,
        theme=settings.theme
    )

# ============================================================================
# SETTINGS
# ============================================================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings_page():
    user = current_user()
    settings = get_user_settings(user)
    
    if request.method == "POST":
        settings.theme = request.form.get("theme", "dark")
        settings.view_mode = request.form.get("view_mode", "grid")
        settings.start_page = request.form.get("start_page", "/")
        settings.trash_auto_delete_days = int(request.form.get("trash_days", 30))
        
        db.session.commit()
        
        log_event(user, "update_settings")
        
        return render_template("settings.html", settings=settings, theme=settings.theme, success="Settings saved successfully")
    
    return render_template("settings.html", settings=settings, theme=settings.theme)

# ============================================================================
# ADMIN
# ============================================================================

@app.route("/admin")
@admin_required
def admin():
    users_data = {}
    total_storage = 0
    total_files = 0
    
    for u in User.query.all():
        files = File.query.filter_by(user_id=u.id, is_deleted=False).all()
        size = sum(f.size for f in files)
        
        # Decrypt user information
        username = get_decrypted_username(u)
        email = get_decrypted_email(u)
        mobile = get_decrypted_mobile(u)
        
        users_data[u.id] = {
            "username": username,
            "email": email or "-",
            "mobile": mobile or "-",
            "storage": format_size(size),
            "quota": format_size(u.storage_quota),
            "files": len(files),
            "created": u.created_at.strftime('%Y-%m-%d') if u.created_at else "-",
            "is_current": u.id == session.get('user_id')
        }
        
        total_storage += size
        total_files += len(files)
    
    analytics = {
        "total_users": len(users_data),
        "total_files": total_files,
        "total_storage_formatted": format_size(total_storage)
    }
    
    settings = get_user_settings(current_user())
    
    return render_template("admin.html", users=users_data, analytics=analytics, theme=settings.theme)

@app.route("/admin/logs/<int:user_id>")
@admin_required
def admin_user_logs(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404)
    
    logs = AuditLog.query.filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(100).all()
    
    username = get_decrypted_username(user)
    
    logs_data = [{
        'id': log.id,
        'action': log.action,
        'details': log.details,
        'ip_address': log.ip_address,
        'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for log in logs]
    
    settings = get_user_settings(current_user())
    
    return render_template(
        "admin_logs.html",
        username=username,
        user_id=user_id,
        logs=logs_data,
        theme=settings.theme
    )

@app.route("/admin/logs/all")
@admin_required
def admin_all_logs():   
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    
    logs_data = []
    for log in logs:
        user = User.query.get(log.user_id) if log.user_id else None
        username = get_decrypted_username(user) if user else "System"
        
        logs_data.append({
            'id': log.id,
            'username': username,
            'user_id': log.user_id,
            'action': log.action,
            'details': log.details,
            'ip_address': log.ip_address,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    settings = get_user_settings(current_user())
    
    return render_template(
        "admin_all_logs.html",
        logs=logs_data,
        theme=settings.theme
    )

@app.route("/admin/set-quota/<int:user_id>", methods=["POST"])
@admin_required
def set_quota(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    quota_mb = int(request.form.get("quota_mb", 1024))
    user.storage_quota = quota_mb * 1024 * 1024  # Convert MB to bytes
    
    db.session.commit()
    
    log_event(current_user(), "set_quota", f"User: {user_id}, Quota: {quota_mb}MB")
    
    return jsonify({"success": True})

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user or user.is_admin:
        return jsonify({"success": False, "message": "Cannot delete admin"}), 403
    
    # Delete all files
    files = File.query.filter_by(user_id=user.id).all()
    for f in files:
        if os.path.exists(f.path):
            os.remove(f.path)
        db.session.delete(f)
    
    # Delete folders
    folders = Folder.query.filter_by(user_id=user.id).all()
    for f in folders:
        db.session.delete(f)
    
    # Add to deleted users
    deleted = DeletedUser(username_hash=user.username_hash)
    db.session.add(deleted)
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    log_event(current_user(), "delete_user", f"User ID: {user_id}")
    
    return redirect("/admin")

@app.route("/paste", methods=["POST"])
@login_required
def paste():
    user = current_user()
    mode = request.form.get("mode")  # 'cut' or 'copy'
    item_type = request.form.get("type")  # 'file' or 'folder'
    item_id = request.form.get("id")
    target_folder_id = request.form.get("folder_id")
    
    target_folder = Folder.query.get(target_folder_id)
    if not target_folder or target_folder.user_id != user.id:
        return jsonify({"success": False, "error": "Invalid target folder"}), 400
    
    if item_type == "file":
        item = File.query.get(item_id)
        if not item or item.user_id != user.id:
            return jsonify({"success": False, "error": "Invalid file"}), 400
        
        if mode == "cut":
            # Move file
            item.folder_id = target_folder.id
            log_event(user, "move_file", f"File ID: {item_id} to folder {target_folder_id}")
        elif mode == "copy":
            # Copy file
            import shutil
            key = get_user_key(user)
            
            # Read and decrypt original file
            with open(item.path, "rb") as f:
                enc_data = f.read()
            dec_data = decrypt_bytes(enc_data, key)
            
            # Encrypt and save copy
            enc_data_copy = encrypt_bytes(dec_data, key)
            storage_name = str(uuid.uuid4())
            new_path = os.path.join(STORAGE_PATH, storage_name)
            
            with open(new_path, "wb") as f:
                f.write(enc_data_copy)
            
            # Create new file entry
            new_file = File(
                user_id=user.id,
                folder_id=target_folder.id,
                name_enc=item.name_enc,
                name_hash=item.name_hash,
                path=new_path,
                size=item.size
            )
            db.session.add(new_file)
            log_event(user, "copy_file", f"File ID: {item_id} to folder {target_folder_id}")
    
    elif item_type == "folder":
        folder = Folder.query.get(item_id)
        if not folder or folder.user_id != user.id:
            return jsonify({"success": False, "error": "Invalid folder"}), 400
        
        if mode == "cut":
            # Move folder
            folder.parent_id = target_folder.id
            log_event(user, "move_folder", f"Folder ID: {item_id} to folder {target_folder_id}")
        elif mode == "copy":
            # Copy folder (not implemented for now)
            return jsonify({"success": False, "error": "Folder copy not yet supported"}), 400
    
    db.session.commit()
    return jsonify({"success": True})

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=2000)