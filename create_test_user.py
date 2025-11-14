"""
Quick script to create a test user in the security service database
"""
import bcrypt
import sqlite3
import os

# Path to the security service database
db_path = "microservices/security-service/src/test.db"

# Test user credentials
username = "testuser"
password = "test123"
roles = "researcher"

# Hash the password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR UNIQUE NOT NULL,
        hashed_password VARCHAR NOT NULL,
        roles VARCHAR
    )
""")

# Check if user already exists
cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
existing = cursor.fetchone()

if existing:
    print(f"❌ User '{username}' already exists with ID {existing[0]}")
else:
    # Insert test user
    cursor.execute(
        "INSERT INTO users (username, hashed_password, roles) VALUES (?, ?, ?)",
        (username, hashed_password, roles)
    )
    conn.commit()
    print(f"✅ Test user created successfully!")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Roles: {roles}")

# List all users
cursor.execute("SELECT id, username, roles FROM users")
users = cursor.fetchall()
print(f"\n📋 All users in database:")
for user in users:
    print(f"   ID: {user[0]}, Username: {user[1]}, Roles: {user[2]}")

conn.close()
