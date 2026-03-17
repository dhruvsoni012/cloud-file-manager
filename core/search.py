from database.models import File, Folder
from crypto.indexer import hash_name
from crypto.text import decrypt_text
from crypto.key_manager import decrypt_key

def search_items(user, query):
    """Search files and folders by name"""
    if len(query) < 2:
        return []
    
    key = decrypt_key(user.encryption_key)
    search_hash = hash_name(query)
    
    # Search files
    files = File.query.filter(
        File.user_id == user.id,
        File.name_hash.contains(search_hash),
        File.is_deleted == False
    ).all()
    
    # Search folders
    folders = Folder.query.filter(
        Folder.user_id == user.id,
        Folder.name_hash.contains(search_hash),
        Folder.is_deleted == False
    ).all()
    
    results = []
    
    # Add files to results
    for f in files:
        folder = Folder.query.get(f.folder_id)
        results.append({
            'type': 'file',
            'id': f.id,
            'name': decrypt_text(f.name_enc, key),
            'location': decrypt_text(folder.name_enc, key) if folder else 'Unknown',
            'folder_id': f.folder_id
        })
    
    # Add folders to results
    for f in folders:
        parent = Folder.query.get(f.parent_id) if f.parent_id else None
        results.append({
            'type': 'folder',
            'id': f.id,
            'name': decrypt_text(f.name_enc, key),
            'location': decrypt_text(parent.name_enc, key) if parent else 'Root',
            'folder_id': f.id
        })
    
    return results