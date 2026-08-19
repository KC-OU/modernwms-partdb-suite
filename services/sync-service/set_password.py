#!/usr/bin/env python3
"""
CLI Utility to securely update the Admin Password for PartDB -> ModernWMS Sync API.
Password is hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and a random salt.
Plaintext passwords are NEVER stored.
"""

import sys
import os
import json
import hashlib
import secrets
import datetime
import getpass

CREDENTIALS_FILE = os.environ.get("CREDENTIALS_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "credentials.json"))

def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex(), salt.hex()

def main():
    print("=" * 60)
    print(" 🔑 PartDB-ModernWMS Sync API Admin Password Configuration")
    print("=" * 60)
    
    current_user = "admin"
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                current_user = json.load(f).get("username", "admin")
        except Exception:
            pass

    username = input(f"Enter admin username [{current_user}]: ").strip() or current_user
    password = getpass.getpass("Enter new strong password: ").strip()
    if len(password) < 6:
        print("❌ Error: Password must be at least 6 characters long.")
        sys.exit(1)
        
    confirm = getpass.getpass("Confirm new password: ").strip()
    if password != confirm:
        print("❌ Error: Passwords do not match.")
        sys.exit(1)
        
    pass_hash, salt_hex = hash_password(password)
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({
            "username": username,
            "password_hash": pass_hash,
            "salt": salt_hex,
            "updated_at": datetime.datetime.now().isoformat()
        }, f, indent=2)
        
    print("\n✅ Password successfully updated and hashed!")
    print(f"📁 Credentials stored securely in: {CREDENTIALS_FILE}")
    print("🔒 Algorithm: PBKDF2-HMAC-SHA256 (100,000 rounds)")
    print("\nPlease restart or recreate the sync container if running: docker-compose restart")

if __name__ == "__main__":
    main()
