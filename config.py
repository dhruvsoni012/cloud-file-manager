import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, "cloud.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-change-this-in-production")
STORAGE_PATH = os.path.join(BASE_DIR, "storage")

# Create storage directory
os.makedirs(STORAGE_PATH, exist_ok=True)