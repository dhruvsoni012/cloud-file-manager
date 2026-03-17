from database.db import db
from database.models import AuditLog
from datetime import datetime

def log_event(user, action, details="", ip=""):
    """Log an audit event"""
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        details=details,
        ip_address=ip,
        timestamp=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()

def get_user_logs(user, limit=50):
    """Get audit logs for a user"""
    return AuditLog.query.filter_by(user_id=user.id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()

def get_all_logs(limit=100):
    """Get all audit logs (admin only)"""
    return AuditLog.query.order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()