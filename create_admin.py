from app import app, db
from core.auth import create_user

with app.app_context():
    print("\n" + "="*50)
    print("   Cloud File Manager - Admin Setup")
    print("="*50 + "\n")
    
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    email = input("Enter admin email (optional): ") or None
    mobile = input("Enter admin mobile (optional): ") or None
    
    ok, msg = create_user(username, password, email, mobile, is_admin=True)
    
    print(f"\n{msg}")
    
    if ok:
        print(f"\n✅ Admin account created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email or 'Not set'}")
        print(f"Mobile: {mobile or 'Not set'}")
        print(f"\nYou can now login at http://localhost:5000/login")
    print()