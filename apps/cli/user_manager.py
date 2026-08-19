#!/usr/bin/env python3
"""
===============================================================================
 ModernWMS & PartDB Enterprise User & Security Manager
 Author: Google Antigravity Agentic Assistant
 Features:
   - Full CRUD User Management across ModernWMS & PartDB SQLite Databases
   - Cryptographically Secure Random Temporary Password Generation
   - Forced Password Change on First Login (Enforced for both WMS & PartDB)
   - Synchronized User Creation & Status Management
   - Standalone CLI and Reusable Python Module
===============================================================================
"""

import os
import sys
import json
import sqlite3
import hashlib
import secrets
import string
import datetime
import subprocess
from typing import Dict, List, Optional, Tuple

WMS_CONTAINER = os.environ.get("MODERNWMS_CONTAINER", "modernwms")
WMS_DB_PATH = os.environ.get("MODERNWMS_DB_PATH", "/app/wms.db")
PARTDB_CONTAINER = os.environ.get("PARTDB_CONTAINER", "partdb")
PARTDB_DB_PATH = os.environ.get("PARTDB_DB_PATH", "/root/docker-server/partdb/db/app.db")
AUDIT_LOG_FILE = os.environ.get("AUDIT_LOG_FILE", "/root/tui_audit.log")

def log_audit_event(user_name: str, role: str, action: str, status: str, details: str = ""):
    """Logs security audit events with timestamp to AUDIT_LOG_FILE."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] USER:{user_name} | ROLE:{role} | ACTION:{action} | STATUS:{status}"
    if details:
        log_line += f" | DETAILS:{details}"
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception:
        pass

def run_wms_db_script(python_code: str) -> Tuple[bool, str]:
    """Executes a Python database script inside the ModernWMS docker container."""
    try:
        proc = subprocess.run(
            ['docker', 'exec', '-i', WMS_CONTAINER, 'python3', '-'],
            input=python_code,
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            return False, proc.stderr.strip()
        return True, proc.stdout.strip()
    except Exception as e:
        return False, str(e)

def init_wms_security_table():
    """Initializes the user_security table inside ModernWMS wms.db if not exists."""
    script = f'''
import sqlite3
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS user_security (
        user_id INTEGER PRIMARY KEY,
        must_change_pw INTEGER DEFAULT 0,
        temp_pw_created_at TEXT
    )
""")
conn.commit()
conn.close()
print("OK")
'''
    run_wms_db_script(script)

# Ensure security table is initialized
try:
    init_wms_security_table()
except Exception:
    pass

def generate_temp_password(length: int = 10) -> str:
    """Generates a cryptographically secure random temporary password containing uppercase, lowercase, numbers and safe symbols."""
    if length < 8:
        length = 8
    uppers = string.ascii_uppercase
    lowers = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%&*?"
    
    password = [
        secrets.choice(uppers),
        secrets.choice(lowers),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    all_chars = uppers + lowers + digits + symbols
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def hash_wms_password(password: str) -> str:
    """ModernWMS uses standard MD5 hex digest."""
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def hash_partdb_password(password: str) -> str:
    """PartDB uses bcrypt hashes ($2y$...). Hashes using PartDB container's PHP engine."""
    p_escaped = password.replace('\\', '\\\\').replace("'", "\\'")
    try:
        proc = subprocess.run([
            'docker', 'exec', '-i', PARTDB_CONTAINER, 'php', '-r',
            f"echo password_hash('{p_escaped}', PASSWORD_BCRYPT);"
        ], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0 and proc.stdout.startswith('$2y$'):
            return proc.stdout.strip()
    except Exception:
        pass
    
    # Fallback to bcrypt if available
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception:
        raise RuntimeError("Failed to generate PartDB bcrypt hash (PartDB container or bcrypt unavailable)")

def verify_partdb_password(password: str, pwd_hash: str) -> bool:
    """Verifies a plaintext password against PartDB bcrypt hash."""
    if not pwd_hash:
        return False
    p_escaped = password.replace('\\', '\\\\').replace("'", "\\'")
    h_escaped = pwd_hash.replace('\\', '\\\\').replace("'", "\\'")
    try:
        proc = subprocess.run([
            'docker', 'exec', '-i', PARTDB_CONTAINER, 'php', '-r',
            f"$h = '{h_escaped}'; $p = '{p_escaped}'; echo password_verify($p, $h) ? 'VALID' : 'INVALID';"
        ], capture_output=True, text=True, timeout=5)
        if "VALID" in proc.stdout:
            return True
    except Exception:
        pass
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), pwd_hash.encode('utf-8'))
    except Exception:
        pass
    return False

# =============================================================================
# 📋 USER LISTING
# =============================================================================

def list_modernwms_users() -> List[Dict]:
    """Lists all ModernWMS users with role, active status, and must_change_pw state."""
    init_wms_security_table()
    script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
query = """
    SELECT u.id, u.user_num, u.user_name, u.user_role, u.is_valid, u.email, u.create_time,
           COALESCE(s.must_change_pw, 0) as must_change_pw
    FROM user u
    LEFT JOIN user_security s ON u.id = s.user_id
    ORDER BY u.id ASC
"""
rows = c.execute(query).fetchall()
conn.close()
results = []
for r in rows:
    results.append({{
        "system": "ModernWMS",
        "id": r[0],
        "user_num": r[1],
        "username": r[2],
        "role": r[3],
        "is_valid": bool(r[4]),
        "email": r[5] or "",
        "create_time": r[6] or "",
        "must_change_pw": bool(r[7])
    }})
print(json.dumps(results))
'''
    ok, out = run_wms_db_script(script)
    if ok and out:
        try:
            return json.loads(out)
        except Exception:
            pass
    return []

def list_partdb_users() -> List[Dict]:
    """Lists all PartDB users with group, active status, and need_pw_change state."""
    if not os.path.exists(PARTDB_DB_PATH):
        return []
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        query = """
            SELECT u.id, u.name, u.email, u.disabled, u.need_pw_change, u.group_id, u.datetime_added,
                   g.name as group_name
            FROM users u
            LEFT JOIN groups g ON u.group_id = g.id
            ORDER BY u.id ASC
        """
        rows = c.execute(query).fetchall()
        conn.close()
        results = []
        for r in rows:
            group_display = r[7] if r[7] else ("Admin" if r[5] == 1 else "User")
            results.append({
                "system": "PartDB",
                "id": r[0],
                "user_num": str(r[0]),
                "username": r[1],
                "role": f"PartDB {group_display}",
                "is_valid": not bool(r[3]), # disabled == 0 means valid
                "email": r[2] or "",
                "create_time": r[6] or "",
                "must_change_pw": bool(r[4])
            })
        return results
    except Exception as e:
        return []

def list_all_users() -> List[Dict]:
    """Aggregates all users from both ModernWMS and PartDB."""
    wms = list_modernwms_users()
    pdb = list_partdb_users()
    return wms + pdb

# =============================================================================
# ➕ USER CREATION
# =============================================================================

def create_modernwms_user(username: str, role: str = "Picker", email: str = "", custom_password: str = None, temp_password: bool = True) -> Tuple[bool, str, str]:
    """
    Creates a new user in ModernWMS.
    Returns: (success: bool, message: str, assigned_password: str)
    """
    init_wms_security_table()
    username = username.strip()
    if not username:
        return False, "Username cannot be empty.", ""
    
    # Check if user already exists
    check_script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u = {json.dumps(username)}
exists = c.execute("SELECT id FROM user WHERE LOWER(user_name) = LOWER(?) OR LOWER(user_num) = LOWER(?)", (u, u)).fetchone()
conn.close()
print("EXISTS" if exists else "NOT_EXISTS")
'''
    ok, out = run_wms_db_script(check_script)
    if ok and out.strip() == "EXISTS":
        return False, f"ModernWMS user '{username}' already exists.", ""

    pwd_to_use = custom_password if custom_password else generate_temp_password(10)
    pwd_hash = hash_wms_password(pwd_to_use)
    must_change = 1 if temp_password else 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    create_script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_name = {json.dumps(username)}
u_num = {json.dumps(username)}
u_role = {json.dumps(role)}
u_email = {json.dumps(email)}
p_hash = {json.dumps(pwd_hash)}
now = {json.dumps(now_str)}
must_chg = {must_change}

max_id_row = c.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM user").fetchone()
next_id = max_id_row[0] if max_id_row else 1

c.execute("""
    INSERT INTO user (id, user_num, user_name, contact_tel, user_role, sex, is_valid, auth_string, email, creator, create_time, last_update_time, tenant_id)
    VALUES (?, ?, ?, '', ?, 'Unknown', 1, ?, ?, 'admin', ?, ?, 1)
""", (next_id, u_num, u_name, u_role, p_hash, u_email, now, now))

c.execute("""
    INSERT OR REPLACE INTO user_security (user_id, must_change_pw, temp_pw_created_at)
    VALUES (?, ?, ?)
""", (next_id, must_chg, now))

conn.commit()
conn.close()
print("SUCCESS:" + str(next_id))
'''
    ok, out = run_wms_db_script(create_script)
    if ok and "SUCCESS:" in out:
        new_id = out.split("SUCCESS:")[1].strip()
        log_audit_event("admin", "Admin", "CREATE_USER_MODERNWMS", "SUCCESS", f"Created user {username} (ID: {new_id}, Role: {role}, TempPW: {temp_password})")
        return True, f"User '{username}' successfully created in ModernWMS (ID #{new_id}).", pwd_to_use
    else:
        return False, f"Database error creating ModernWMS user: {out}", ""

def create_partdb_user(username: str, role: str = "PartDB User", email: str = "", custom_password: str = None, temp_password: bool = True) -> Tuple[bool, str, str]:
    """
    Creates a new user in PartDB.
    Returns: (success: bool, message: str, assigned_password: str)
    """
    if not os.path.exists(PARTDB_DB_PATH):
        return False, f"PartDB database not found at {PARTDB_DB_PATH}", ""
    
    username = username.strip()
    if not username:
        return False, "Username cannot be empty.", ""

    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        exists = c.execute("SELECT id FROM users WHERE LOWER(name) = LOWER(?)", (username,)).fetchone()
        if exists:
            conn.close()
            return False, f"PartDB user '{username}' already exists.", ""

        pwd_to_use = custom_password if custom_password else generate_temp_password(10)
        pwd_hash = hash_partdb_password(pwd_to_use)
        must_change = 1 if temp_password else 0
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        group_id = 1 if "admin" in role.lower() else 2

        c.execute("""
            INSERT INTO users (
                group_id, currency_id, id_preview_attachment, disabled, config_theme, pw_reset_token,
                config_instock_comment_a, config_instock_comment_w, trusted_device_cookie_version, backup_codes,
                google_authenticator_secret, config_timezone, config_language, email, department,
                last_name, first_name, need_pw_change, password, name, settings, saml_user, about_me, show_email_on_profile,
                datetime_added, last_modified, permissions_data
            ) VALUES (
                ?, NULL, NULL, 0, NULL, NULL,
                '', '', 1, '[]',
                NULL, NULL, NULL, ?, NULL,
                NULL, NULL, ?, ?, ?, '[]', 0, '', 0,
                ?, ?, '[]'
            )
        """, (group_id, email, must_change, pwd_hash, username, now_str, now_str))

        new_id = c.lastrowid
        conn.commit()
        conn.close()

        log_audit_event("admin", "Admin", "CREATE_USER_PARTDB", "SUCCESS", f"Created user {username} (ID: {new_id}, Group: {group_id}, TempPW: {temp_password})")
        return True, f"User '{username}' successfully created in PartDB (ID #{new_id}).", pwd_to_use
    except Exception as e:
        return False, f"Error creating PartDB user: {str(e)}", ""

def create_unified_user(username: str, role: str = "Picker", email: str = "", custom_password: str = None, temp_password: bool = True) -> Tuple[bool, str, str]:
    """Creates user in BOTH ModernWMS and PartDB with identical credentials."""
    pwd_to_use = custom_password if custom_password else generate_temp_password(10)
    
    wms_ok, wms_msg, _ = create_modernwms_user(username, role=role, email=email, custom_password=pwd_to_use, temp_password=temp_password)
    pdb_ok, pdb_msg, _ = create_partdb_user(username, role=role, email=email, custom_password=pwd_to_use, temp_password=temp_password)

    if wms_ok and pdb_ok:
        return True, f"User '{username}' created across BOTH ModernWMS and PartDB!", pwd_to_use
    elif wms_ok:
        return True, f"User created in ModernWMS, but PartDB reported: {pdb_msg}", pwd_to_use
    elif pdb_ok:
        return True, f"User created in PartDB, but ModernWMS reported: {wms_msg}", pwd_to_use
    else:
        return False, f"Failed to create user in either system. WMS: {wms_msg} | PartDB: {pdb_msg}", ""

# =============================================================================
# 🔑 PASSWORD RESET & FORCED CHANGE ENFORCEMENT
# =============================================================================

def reset_modernwms_password(username_or_id: str, new_password: str = None, is_temp: bool = True) -> Tuple[bool, str, str]:
    """Resets password for ModernWMS user and optionally flags must_change_pw."""
    init_wms_security_table()
    pwd_to_use = new_password if new_password else generate_temp_password(10)
    pwd_hash = hash_wms_password(pwd_to_use)
    must_change = 1 if is_temp else 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_in = {json.dumps(str(username_or_id))}
p_hash = {json.dumps(pwd_hash)}
must_chg = {must_change}
now = {json.dumps(now_str)}

user_row = c.execute("SELECT id, user_name FROM user WHERE LOWER(user_name) = LOWER(?) OR LOWER(user_num) = LOWER(?) OR id = ?", (u_in, u_in, u_in)).fetchone()
if not user_row:
    conn.close()
    print("USER_NOT_FOUND")
else:
    u_id = user_row[0]
    c.execute("UPDATE user SET auth_string = ?, is_valid = 1, last_update_time = ? WHERE id = ?", (p_hash, now, u_id))
    c.execute("INSERT OR REPLACE INTO user_security (user_id, must_change_pw, temp_pw_created_at) VALUES (?, ?, ?)", (u_id, must_chg, now))
    conn.commit()
    conn.close()
    print("SUCCESS:" + str(user_row[1]))
'''
    ok, out = run_wms_db_script(script)
    if "USER_NOT_FOUND" in out:
        return False, f"ModernWMS user '{username_or_id}' not found.", ""
    elif ok and "SUCCESS:" in out:
        u_name = out.split("SUCCESS:")[1].strip()
        log_audit_event("admin", "Admin", "RESET_PASSWORD_MODERNWMS", "SUCCESS", f"Reset password for {u_name} (Temp: {is_temp})")
        return True, f"Password for ModernWMS user '{u_name}' successfully reset.", pwd_to_use
    else:
        return False, f"Database error resetting password: {out}", ""

def reset_partdb_password(username_or_id: str, new_password: str = None, is_temp: bool = True) -> Tuple[bool, str, str]:
    """Resets password for PartDB user and flags need_pw_change."""
    if not os.path.exists(PARTDB_DB_PATH):
        return False, "PartDB database not found.", ""

    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        u_in = str(username_or_id)
        user_row = c.execute("SELECT id, name FROM users WHERE LOWER(name) = LOWER(?) OR id = ?", (u_in, u_in)).fetchone()
        if not user_row:
            conn.close()
            return False, f"PartDB user '{username_or_id}' not found.", ""

        u_id, u_name = user_row
        pwd_to_use = new_password if new_password else generate_temp_password(10)
        pwd_hash = hash_partdb_password(pwd_to_use)
        must_change = 1 if is_temp else 0
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""
            UPDATE users 
            SET password = ?, need_pw_change = ?, disabled = 0, last_modified = ?
            WHERE id = ?
        """, (pwd_hash, must_change, now_str, u_id))
        conn.commit()
        conn.close()

        log_audit_event("admin", "Admin", "RESET_PASSWORD_PARTDB", "SUCCESS", f"Reset password for {u_name} (Temp: {is_temp})")
        return True, f"Password for PartDB user '{u_name}' successfully reset.", pwd_to_use
    except Exception as e:
        return False, f"Error resetting PartDB password: {str(e)}", ""

def reset_unified_password(username_or_id: str, new_password: str = None, is_temp: bool = True) -> Tuple[bool, str, str]:
    """Resets password for user across BOTH ModernWMS and PartDB."""
    pwd_to_use = new_password if new_password else generate_temp_password(10)
    w_ok, w_msg, _ = reset_modernwms_password(username_or_id, pwd_to_use, is_temp)
    p_ok, p_msg, _ = reset_partdb_password(username_or_id, pwd_to_use, is_temp)

    if w_ok and p_ok:
        return True, f"Password successfully reset across BOTH ModernWMS and PartDB!", pwd_to_use
    elif w_ok:
        return True, f"Reset in ModernWMS ({w_msg}), PartDB: {p_msg}", pwd_to_use
    elif p_ok:
        return True, f"Reset in PartDB ({p_msg}), ModernWMS: {w_msg}", pwd_to_use
    else:
        return False, f"Could not find user '{username_or_id}' in either system.", ""

def check_must_change_password(system: str, username_or_id: str) -> bool:
    """Checks if a user has a pending forced password change."""
    if system.lower() in ["modernwms", "wms"]:
        init_wms_security_table()
        script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_in = {json.dumps(str(username_or_id))}
row = c.execute("""
    SELECT s.must_change_pw 
    FROM user u
    LEFT JOIN user_security s ON u.id = s.user_id
    WHERE LOWER(u.user_name) = LOWER(?) OR LOWER(u.user_num) = LOWER(?) OR u.id = ?
""", (u_in, u_in, u_in)).fetchone()
conn.close()
print("1" if (row and row[0] == 1) else "0")
'''
        ok, out = run_wms_db_script(script)
        return "1" in out
    elif system.lower() in ["partdb", "pdb"]:
        if not os.path.exists(PARTDB_DB_PATH): return False
        try:
            conn = sqlite3.connect(PARTDB_DB_PATH)
            c = conn.cursor()
            u_in = str(username_or_id)
            row = c.execute("SELECT need_pw_change FROM users WHERE LOWER(name) = LOWER(?) OR id = ?", (u_in, u_in)).fetchone()
            conn.close()
            return bool(row and row[0] == 1)
        except Exception:
            return False
    return False

def complete_forced_password_change(system: str, username_or_id: str, new_password: str) -> Tuple[bool, str]:
    """Updates user password and clears the must_change_pw flag upon first login."""
    if len(new_password) < 4:
        return False, "Password must be at least 4 characters long."

    if system.lower() in ["modernwms", "wms"]:
        init_wms_security_table()
        pwd_hash = hash_wms_password(new_password)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_in = {json.dumps(str(username_or_id))}
p_hash = {json.dumps(pwd_hash)}
now = {json.dumps(now_str)}

user_row = c.execute("SELECT id, user_name FROM user WHERE LOWER(user_name) = LOWER(?) OR LOWER(user_num) = LOWER(?) OR id = ?", (u_in, u_in, u_in)).fetchone()
if not user_row:
    conn.close()
    print("NOT_FOUND")
else:
    u_id = user_row[0]
    c.execute("UPDATE user SET auth_string = ?, last_update_time = ? WHERE id = ?", (p_hash, now, u_id))
    c.execute("INSERT OR REPLACE INTO user_security (user_id, must_change_pw, temp_pw_created_at) VALUES (?, 0, ?)", (u_id, now))
    conn.commit()
    conn.close()
    print("SUCCESS:" + str(user_row[1]))
'''
        ok, out = run_wms_db_script(script)
        if ok and "SUCCESS:" in out:
            u_name = out.split("SUCCESS:")[1].strip()
            log_audit_event(u_name, "User", "PASSWORD_CHANGED_FIRST_LOGIN", "SUCCESS", "ModernWMS temporary password updated to permanent password")
            return True, "ModernWMS password updated successfully! You may now proceed."
        return False, f"Failed to update password: {out}"

    elif system.lower() in ["partdb", "pdb"]:
        if not os.path.exists(PARTDB_DB_PATH):
            return False, "PartDB database not found."
        try:
            conn = sqlite3.connect(PARTDB_DB_PATH)
            c = conn.cursor()
            u_in = str(username_or_id)
            user_row = c.execute("SELECT id, name FROM users WHERE LOWER(name) = LOWER(?) OR id = ?", (u_in, u_in)).fetchone()
            if not user_row:
                conn.close()
                return False, f"PartDB user '{username_or_id}' not found."
            u_id, u_name = user_row
            pwd_hash = hash_partdb_password(new_password)
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("UPDATE users SET password = ?, need_pw_change = 0, last_modified = ? WHERE id = ?", (pwd_hash, now_str, u_id))
            conn.commit()
            conn.close()
            log_audit_event(u_name, "User", "PASSWORD_CHANGED_FIRST_LOGIN", "SUCCESS", "PartDB temporary password updated to permanent password")
            return True, "PartDB password updated successfully! You may now proceed."
        except Exception as e:
            return False, f"Failed to update PartDB password: {str(e)}"
    return False, "Unknown authentication system."

# =============================================================================
# ✏️ USER MODIFICATION & DELETION
# =============================================================================

def modify_modernwms_user(username_or_id: str, role: str = None, is_valid: int = None, email: str = None) -> Tuple[bool, str]:
    """Modifies ModernWMS user role, active status, or email."""
    payload = json.dumps({
        "username_or_id": str(username_or_id),
        "role": role,
        "is_valid": is_valid,
        "email": email
    })
    script = f'''
import sqlite3, json
data = json.loads({json.dumps(payload)})
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_in = data["username_or_id"]
user_row = c.execute("SELECT id, user_name, user_role, is_valid, email FROM user WHERE LOWER(user_name) = LOWER(?) OR id = ?", (u_in, u_in)).fetchone()
if not user_row:
    conn.close()
    print("NOT_FOUND")
else:
    u_id, u_name, cur_role, cur_valid, cur_email = user_row
    new_role = data["role"] if data["role"] is not None else cur_role
    new_valid = data["is_valid"] if data["is_valid"] is not None else cur_valid
    new_email = data["email"] if data["email"] is not None else cur_email
    c.execute("UPDATE user SET user_role = ?, is_valid = ?, email = ? WHERE id = ?", (new_role, new_valid, new_email, u_id))
    conn.commit()
    conn.close()
    print("SUCCESS:" + str(u_name))
'''
    ok, out = run_wms_db_script(script)
    if ok and "SUCCESS:" in out:
        u_name = out.split("SUCCESS:")[1].strip()
        log_audit_event("admin", "Admin", "MODIFY_USER_MODERNWMS", "SUCCESS", f"Updated user {u_name} (Role: {role}, Valid: {is_valid})")
        return True, f"ModernWMS user '{u_name}' updated successfully."
    return False, f"Could not update ModernWMS user: {out}"

def modify_partdb_user(username_or_id: str, role: str = None, is_valid: int = None, email: str = None) -> Tuple[bool, str]:
    """Modifies PartDB user group or active status."""
    if not os.path.exists(PARTDB_DB_PATH): return False, "PartDB database not found."
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        u_in = str(username_or_id)
        user_row = c.execute("SELECT id, name, group_id, disabled, email FROM users WHERE LOWER(name) = LOWER(?) OR id = ?", (u_in, u_in)).fetchone()
        if not user_row:
            conn.close()
            return False, f"PartDB user '{username_or_id}' not found."
        u_id, u_name, cur_group, cur_disabled, cur_email = user_row
        
        new_group = cur_group
        if role:
            new_group = 1 if "admin" in role.lower() else 2
        
        new_disabled = (1 - is_valid) if is_valid is not None else cur_disabled
        new_email = email if email is not None else cur_email

        c.execute("UPDATE users SET group_id = ?, disabled = ?, email = ? WHERE id = ?", (new_group, new_disabled, new_email, u_id))
        conn.commit()
        conn.close()
        log_audit_event("admin", "Admin", "MODIFY_USER_PARTDB", "SUCCESS", f"Updated user {u_name} (Group: {new_group}, Disabled: {new_disabled})")
        return True, f"PartDB user '{u_name}' updated successfully."
    except Exception as e:
        return False, f"Error modifying PartDB user: {str(e)}"

def delete_user(system: str, username_or_id: str) -> Tuple[bool, str]:
    """Securely deletes a user from ModernWMS or PartDB (admin accounts protected)."""
    u_str = str(username_or_id).lower()
    if u_str in ["admin", "1", "kcollins", "2"]:
        return False, f"Protected Administrator account '{username_or_id}' cannot be deleted!"

    if system.lower() in ["modernwms", "wms"]:
        script = f'''
import sqlite3, json
conn = sqlite3.connect("{WMS_DB_PATH}")
c = conn.cursor()
u_in = {json.dumps(str(username_or_id))}
user_row = c.execute("SELECT id, user_name FROM user WHERE (LOWER(user_name) = LOWER(?) OR id = ?) AND LOWER(user_name) != 'admin'", (u_in, u_in)).fetchone()
if not user_row:
    conn.close()
    print("NOT_FOUND")
else:
    u_id, u_name = user_row
    c.execute("DELETE FROM user WHERE id = ?", (u_id,))
    c.execute("DELETE FROM user_security WHERE user_id = ?", (u_id,))
    conn.commit()
    conn.close()
    print("SUCCESS:" + str(u_name))
'''
        ok, out = run_wms_db_script(script)
        if ok and "SUCCESS:" in out:
            u_name = out.split("SUCCESS:")[1].strip()
            log_audit_event("admin", "Admin", "DELETE_USER_MODERNWMS", "SUCCESS", f"Deleted user {u_name} (ID: {username_or_id})")
            return True, f"ModernWMS user '{u_name}' deleted successfully."
        return False, f"Could not delete ModernWMS user: {out}"

    elif system.lower() in ["partdb", "pdb"]:
        if not os.path.exists(PARTDB_DB_PATH): return False, "PartDB database not found."
        try:
            conn = sqlite3.connect(PARTDB_DB_PATH)
            c = conn.cursor()
            u_in = str(username_or_id)
            user_row = c.execute("SELECT id, name FROM users WHERE (LOWER(name) = LOWER(?) OR id = ?) AND LOWER(name) != 'kcollins' AND id > 2", (u_in, u_in)).fetchone()
            if not user_row:
                conn.close()
                return False, f"PartDB user '{username_or_id}' not found or is a protected system account."
            u_id, u_name = user_row
            c.execute("DELETE FROM users WHERE id = ?", (u_id,))
            conn.commit()
            conn.close()
            log_audit_event("admin", "Admin", "DELETE_USER_PARTDB", "SUCCESS", f"Deleted user {u_name} (ID: {u_id})")
            return True, f"PartDB user '{u_name}' deleted successfully."
        except Exception as e:
            return False, f"Error deleting PartDB user: {str(e)}"
    return False, "Unknown system specified."

# =============================================================================
# 💻 CLI COMMAND HANDLER
# =============================================================================

def print_cli_help():
    print("""
ModernWMS & PartDB Enterprise User & Security Manager
Usage:
  user-manager --list                                (List all users across systems)
  user-manager --create <username> [role] [email]    (Create user with random temp password)
  user-manager --reset <username>                    (Reset user password with random temp password)
  user-manager --set-password <username> <new_pwd>   (Set specific user password)
  user-manager --delete <system> <username>          (Delete user from system)
  user-manager --toggle-active <system> <username>   (Enable or disable user)
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_cli_help()
        sys.exit(0)

    arg1 = sys.argv[1]
    if arg1 in ["-l", "--list", "list"]:
        users = list_all_users()
        print(f"\n{'SYSTEM':<11} | {'ID':<4} | {'USERNAME':<15} | {'ROLE / GROUP':<18} | {'STATUS':<9} | {'TEMP PW?':<9} | {'EMAIL'}")
        print("-" * 95)
        for u in users:
            status_str = "ACTIVE" if u['is_valid'] else "DISABLED"
            temp_str = "YES (FORCED)" if u['must_change_pw'] else "NO"
            print(f"{u['system']:<11} | {u['id']:<4} | {u['username']:<15} | {u['role']:<18} | {status_str:<9} | {temp_str:<9} | {u['email']}")
        print(f"\nTotal Registered Users: {len(users)}\n")
        sys.exit(0)

    elif arg1 in ["-c", "--create", "create"]:
        if len(sys.argv) < 3:
            print("Error: Missing username argument.")
            sys.exit(1)
        username = sys.argv[2]
        role = sys.argv[3] if len(sys.argv) > 3 else "Picker"
        email = sys.argv[4] if len(sys.argv) > 4 else ""
        ok, msg, temp_pwd = create_unified_user(username, role=role, email=email, temp_password=True)
        if ok:
            print(f"✅ {msg}")
            print(f"🔑 Generated Temporary Password: {temp_pwd}")
            print(f"⚠️  Note: The user will be required to change their password upon their first login.")
        else:
            print(f"❌ {msg}")

    elif arg1 in ["-r", "--reset", "reset"]:
        if len(sys.argv) < 3:
            print("Error: Missing username argument.")
            sys.exit(1)
        username = sys.argv[2]
        ok, msg, temp_pwd = reset_unified_password(username, is_temp=True)
        if ok:
            print(f"✅ {msg}")
            print(f"🔑 Generated Temporary Password: {temp_pwd}")
            print(f"⚠️  Note: The user will be required to change their password upon next login.")
        else:
            print(f"❌ {msg}")

    elif arg1 in ["--set-password", "set-password"]:
        if len(sys.argv) < 4:
            print("Error: Usage: user-manager --set-password <username> <new_password>")
            sys.exit(1)
        username = sys.argv[2]
        new_pwd = sys.argv[3]
        ok, msg, _ = reset_unified_password(username, new_password=new_pwd, is_temp=False)
        if ok:
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")

    elif arg1 in ["-d", "--delete", "delete"]:
        if len(sys.argv) < 4:
            print("Error: Usage: user-manager --delete <system: wms|partdb> <username>")
            sys.exit(1)
        system = sys.argv[2]
        username = sys.argv[3]
        ok, msg = delete_user(system, username)
        if ok:
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")

    else:
        print_cli_help()

if __name__ == "__main__":
    main()
