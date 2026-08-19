#!/usr/bin/env python3
"""
ModernWMS SQLite Database Automated Backup Script
Extracts a clean SQLite backup from the modernwms docker container to /root/backups/modernwms/
"""

import os
import sys
import datetime
import subprocess

CONTAINER = os.environ.get("MODERNWMS_CONTAINER", "modernwms")
DB_PATH = os.environ.get("MODERNWMS_DB_PATH", "/app/wms.db")
BACKUP_DIR = os.environ.get("MODERNWMS_BACKUP_DIR", "/root/backups/modernwms")

def create_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_file = os.path.join(BACKUP_DIR, f"modernwms_db_{timestamp}.db")

    print(f"📦 Initiating ModernWMS database backup...")
    
    # Run sqlite3 backup inside container
    script = f'''
import sqlite3

src = sqlite3.connect("{DB_PATH}")
dst = sqlite3.connect("/tmp/backup.db")
src.backup(dst)
dst.close()
src.close()
print("BACKUP_SUCCESS")
'''
    proc = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'python3', '-'], input=script, capture_output=True, text=True)
    if "BACKUP_SUCCESS" not in proc.stdout:
        print("❌ Error creating database dump inside container:", proc.stderr)
        return None

    # Copy backup out of container
    cp_proc = subprocess.run(['docker', 'cp', f'{CONTAINER}:/tmp/backup.db', target_file], capture_output=True, text=True)
    subprocess.run(['docker', 'exec', CONTAINER, 'rm', '-f', '/tmp/backup.db'], capture_output=True, text=True)

    if cp_proc.returncode == 0 and os.path.exists(target_file):
        size_kb = os.path.getsize(target_file) / 1024.0
        print(f"✅ Backup created successfully!")
        print(f"   File: {target_file}")
        print(f"   Size: {size_kb:.2f} KB")
        return target_file
    else:
        print("❌ Error copying backup file to host:", cp_proc.stderr)
        return None

if __name__ == "__main__":
    create_backup()
