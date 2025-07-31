# hash_admin_password.py
from utils import hash_password

plain_password = "admin123"
hashed = hash_password(plain_password)
print("Hashed password:", hashed)
