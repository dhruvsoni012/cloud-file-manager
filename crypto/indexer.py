import hashlib

def hash_name(name):
    """Hash a filename/foldername for search indexing"""
    return hashlib.sha256(name.lower().encode()).hexdigest()

def hash_username(username):
    """Hash username for login lookup"""
    return hashlib.sha256(username.lower().encode()).hexdigest()