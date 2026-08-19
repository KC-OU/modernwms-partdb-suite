#!/usr/bin/env python3
"""
===============================================================================
 ModernWMS & PartDB Enterprise Control Suite & Script Hub (Touch & Tablet Edition)
 Author: Google Antigravity Agentic Assistant
 Security: Dual Authentication (ModernWMS & PartDB SQLite Database Verification)
 Features:
   1. Touch Screen / Tablet Support (XTerm Mouse 1006 SGR Coordinate Engine)
   2. Instant Back / Exit Navigation ('Q' / 'B' / ESC key - No Ctrl+Z needed!)
   3. Multi-Level Action History & Undo Stack ('U' key / [ ↺ Undo ] button)
   4. Touch Quick Add Overlay Drawer ('+' key / [ ➕ Quick Add ])
   5. On-Screen Touch NumPad Overlay for numeric data entry on tablets
   6. Touch Table Row Selection & Pagination
   7. Dual Visual Themes (Cyberpunk & Modern Slate)
   8. PartDB Terminal Creator & ModernWMS WMS Operations
===============================================================================
"""

import os
import sys
import glob
import json
import time
import tty
import termios
import select
import atexit
import getpass
import hashlib
import sqlite3
import datetime
import subprocess
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/root/scripts")
import user_manager

CONTAINER = os.environ.get("MODERNWMS_CONTAINER", "modernwms")
DB_PATH = os.environ.get("MODERNWMS_DB_PATH", "/app/wms.db")
PARTDB_DB_PATH = os.environ.get("PARTDB_DB_PATH", "/root/docker-server/partdb/db/app.db")
SCRIPTS_DIR = os.environ.get("SCRIPTS_DIR", os.path.dirname(os.path.abspath(__file__)))
AUDIT_LOG_FILE = os.environ.get("AUDIT_LOG_FILE", "/root/tui_audit.log")

# =============================================================================
# 🎨 COLOR SCHEMES & DUAL VISUAL THEMES
# =============================================================================

CLR_RESET   = "\033[0m"
C_RESET     = CLR_RESET
CLR_BOLD    = "\033[1m"
C_BOLD      = CLR_BOLD
CLR_DIM     = "\033[2m"
C_DIM       = CLR_DIM
CLR_ITALIC  = "\033[3m"
CLR_UNDER   = "\033[4m"

THEMES = {
    "cyberpunk": {
        "CYAN": "\033[38;5;51m",
        "BLUE": "\033[38;5;39m",
        "GREEN": "\033[38;5;48m",
        "YELLOW": "\033[38;5;220m",
        "RED": "\033[38;5;196m",
        "PURPLE": "\033[38;5;141m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;242m",
        "ORANGE": "\033[38;5;208m",
        "BG_BLUE": "\033[48;5;19m",
        "BG_CYAN": "\033[48;5;31m",
        "BG_DARK": "\033[48;5;236m",
        "BG_RED": "\033[48;5;52m",
        "BG_GREEN": "\033[48;5;22m",
        "BG_YELLOW": "\033[48;5;58m",
        "BG_PURPLE": "\033[48;5;53m"
    },
    "slate": {
        "CYAN": "\033[38;5;38m",
        "BLUE": "\033[38;5;32m",
        "GREEN": "\033[38;5;42m",
        "YELLOW": "\033[38;5;214m",
        "RED": "\033[38;5;203m",
        "PURPLE": "\033[38;5;135m",
        "WHITE": "\033[38;5;254m",
        "GRAY": "\033[38;5;245m",
        "ORANGE": "\033[38;5;215m",
        "BG_BLUE": "\033[48;5;24m",
        "BG_CYAN": "\033[48;5;30m",
        "BG_DARK": "\033[48;5;235m",
        "BG_RED": "\033[48;5;88m",
        "BG_GREEN": "\033[48;5;28m",
        "BG_YELLOW": "\033[48;5;136m",
        "BG_PURPLE": "\033[48;5;54m"
    },
    "dracula": {
        "CYAN": "\033[38;5;117m",
        "BLUE": "\033[38;5;141m",
        "GREEN": "\033[38;5;84m",
        "YELLOW": "\033[38;5;228m",
        "RED": "\033[38;5;203m",
        "PURPLE": "\033[38;5;212m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;242m",
        "ORANGE": "\033[38;5;215m",
        "BG_BLUE": "\033[48;5;61m",
        "BG_CYAN": "\033[48;5;30m",
        "BG_DARK": "\033[48;5;236m",
        "BG_RED": "\033[48;5;88m",
        "BG_GREEN": "\033[48;5;22m",
        "BG_YELLOW": "\033[48;5;58m",
        "BG_PURPLE": "\033[48;5;53m"
    },
    "half-life": {
        "CYAN": "\033[38;5;51m",
        "BLUE": "\033[38;5;39m",
        "GREEN": "\033[38;5;118m",
        "YELLOW": "\033[38;5;214m",
        "RED": "\033[38;5;196m",
        "PURPLE": "\033[38;5;172m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;240m",
        "ORANGE": "\033[38;5;208m",
        "BG_BLUE": "\033[48;5;24m",
        "BG_CYAN": "\033[48;5;31m",
        "BG_DARK": "\033[48;5;235m",
        "BG_RED": "\033[48;5;52m",
        "BG_GREEN": "\033[48;5;28m",
        "BG_YELLOW": "\033[48;5;130m",
        "BG_PURPLE": "\033[48;5;94m"
    },
    "nord": {
        "CYAN": "\033[38;5;110m",
        "BLUE": "\033[38;5;68m",
        "GREEN": "\033[38;5;108m",
        "YELLOW": "\033[38;5;179m",
        "RED": "\033[38;5;131m",
        "PURPLE": "\033[38;5;139m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;243m",
        "ORANGE": "\033[38;5;173m",
        "BG_BLUE": "\033[48;5;24m",
        "BG_CYAN": "\033[48;5;31m",
        "BG_DARK": "\033[48;5;236m",
        "BG_RED": "\033[48;5;52m",
        "BG_GREEN": "\033[48;5;22m",
        "BG_YELLOW": "\033[48;5;58m",
        "BG_PURPLE": "\033[48;5;53m"
    },
    "gruvbox": {
        "CYAN": "\033[38;5;109m",
        "BLUE": "\033[38;5;108m",
        "GREEN": "\033[38;5;142m",
        "YELLOW": "\033[38;5;214m",
        "RED": "\033[38;5;167m",
        "PURPLE": "\033[38;5;175m",
        "WHITE": "\033[38;5;223m",
        "GRAY": "\033[38;5;244m",
        "ORANGE": "\033[38;5;208m",
        "BG_BLUE": "\033[48;5;24m",
        "BG_CYAN": "\033[48;5;30m",
        "BG_DARK": "\033[48;5;235m",
        "BG_RED": "\033[48;5;88m",
        "BG_GREEN": "\033[48;5;100m",
        "BG_YELLOW": "\033[48;5;136m",
        "BG_PURPLE": "\033[48;5;96m"
    },
    "catppuccin": {
        "CYAN": "\033[38;5;117m",
        "BLUE": "\033[38;5;111m",
        "GREEN": "\033[38;5;120m",
        "YELLOW": "\033[38;5;222m",
        "RED": "\033[38;5;211m",
        "PURPLE": "\033[38;5;183m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;245m",
        "ORANGE": "\033[38;5;216m",
        "BG_BLUE": "\033[48;5;25m",
        "BG_CYAN": "\033[48;5;31m",
        "BG_DARK": "\033[48;5;236m",
        "BG_RED": "\033[48;5;88m",
        "BG_GREEN": "\033[48;5;28m",
        "BG_YELLOW": "\033[48;5;136m",
        "BG_PURPLE": "\033[48;5;55m"
    },
    "tokyo_night": {
        "CYAN": "\033[38;5;117m",
        "BLUE": "\033[38;5;75m",
        "GREEN": "\033[38;5;120m",
        "YELLOW": "\033[38;5;221m",
        "RED": "\033[38;5;204m",
        "PURPLE": "\033[38;5;177m",
        "WHITE": "\033[38;5;255m",
        "GRAY": "\033[38;5;242m",
        "ORANGE": "\033[38;5;215m",
        "BG_BLUE": "\033[48;5;24m",
        "BG_CYAN": "\033[48;5;30m",
        "BG_DARK": "\033[48;5;234m",
        "BG_RED": "\033[48;5;88m",
        "BG_GREEN": "\033[48;5;28m",
        "BG_YELLOW": "\033[48;5;130m",
        "BG_PURPLE": "\033[48;5;54m"
    }
}

ACTIVE_THEME_NAME = "cyberpunk"

def get_theme_colors():
    return THEMES.get(ACTIVE_THEME_NAME, THEMES["cyberpunk"])

def update_color_globals():
    global C_CYAN, C_BLUE, C_GREEN, C_YELLOW, C_RED, C_PURPLE, C_WHITE, C_GRAY, C_ORANGE
    global BG_BLUE, BG_CYAN, BG_DARK, BG_RED, BG_GREEN, BG_YELLOW, BG_PURPLE
    t = get_theme_colors()
    C_CYAN   = t["CYAN"]
    C_BLUE   = t["BLUE"]
    C_GREEN  = t["GREEN"]
    C_YELLOW = t["YELLOW"]
    C_RED    = t["RED"]
    C_PURPLE = t["PURPLE"]
    C_WHITE  = t["WHITE"]
    C_GRAY   = t["GRAY"]
    C_ORANGE = t["ORANGE"]
    BG_BLUE  = t["BG_BLUE"]
    BG_CYAN  = t["BG_CYAN"]
    BG_DARK  = t["BG_DARK"]
    BG_RED   = t["BG_RED"]
    BG_GREEN = t["BG_GREEN"]
    BG_YELLOW= t["BG_YELLOW"]
    BG_PURPLE= t["BG_PURPLE"]

update_color_globals()

# Icons
ICO_BOX    = "📦"
ICO_GEAR   = "⚙️"
ICO_LOCK   = "🔒"
ICO_WH     = "🏭"
ICO_TRUCK  = "🚚"
ICO_DOCKER = "🐳"
ICO_USER   = "👤"
ICO_WARN   = "⚠️"
ICO_CHECK  = "✅"
ICO_CROSS  = "❌"
ICO_EYE    = "👁️"
ICO_CHART  = "📊"
ICO_SEARCH = "🔍"
ICO_ALERT  = "🚨"
ICO_SHIELD = "🛡️"
ICO_SCRIPT = "⚡"
ICO_PART   = "🔩"
ICO_UNDO   = "↺"
ICO_ADD    = "➕"
ICO_THEME  = "🎨"
ICO_BACK   = "🔙"

# =============================================================================
# ↺ MULTI-LEVEL UNDO STACK ENGINE
# =============================================================================

class UndoStack:
    """Manages an undo stack of database mutations for easy 1-tap/1-key reversal."""
    def __init__(self):
        self.stack = []

    def push(self, description: str, undo_func):
        self.stack.append((description, undo_func))

    def undo(self) -> tuple:
        if not self.stack:
            return False, "No actions to undo!"
        desc, undo_func = self.stack.pop()
        try:
            res = undo_func()
            return True, f"Undone: {desc}"
        except Exception as e:
            return False, f"Undo failed for '{desc}': {str(e)}"

# =============================================================================
# 👆 TOUCH INPUT & HITBOX COORDINATE MANAGEMENT ENGINE
# =============================================================================

class TouchInputEngine:
    """Handles XTerm 1006 SGR mouse coordinate parsing, hitboxes, and non-blocking input."""
    def __init__(self):
        self.mouse_enabled = False
        self.hitboxes = []  # List of tuples: (y_min, y_max, x_min, x_max, payload)
        self.undo_stack = UndoStack()
        self.active_toast = ""
        self.toast_is_error = False
        self.toast_time = 0

    def enable_mouse(self):
        # We intentionally do not send \\033[?1000h\\033[?1006h to prevent terminal SGR escape noise ([<0;46;15m)
        self.mouse_enabled = False

    def disable_mouse(self):
        if sys.stdin.isatty():
            sys.stdout.write("\033[?1000l\033[?1006l")
            sys.stdout.flush()
        self.mouse_enabled = False

    def clear_hitboxes(self):
        self.hitboxes.clear()

    def register_hitbox(self, y_min: int, y_max: int, x_min: int, x_max: int, payload: str):
        self.hitboxes.append((y_min, y_max, x_min, x_max, payload))

    def find_hitbox(self, y: int, x: int) -> str:
        for y_min, y_max, x_min, x_max, payload in self.hitboxes:
            if y_min <= y <= y_max and x_min <= x <= x_max:
                return payload
        return None

    def show_toast(self, message: str, is_error: bool = False):
        self.active_toast = message
        self.toast_is_error = is_error
        self.toast_time = time.time()

    def read_char_or_touch(self, timeout=None) -> tuple:
        """Reads a single keypress or input sequence cleanly.
        Returns: ('KEY', char), ('HITBOX', payload), or ('TIMEOUT', None)
        """
        if not sys.stdin.isatty():
            line = sys.stdin.readline()
            if not line:
                return ('KEY', 'q')
            return ('KEY', line.strip())

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            if timeout is not None:
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if not rlist:
                    return ('TIMEOUT', None)

            ch = sys.stdin.read(1)
            
            # Catch stray unescaped SGR mouse sequence fragment starting with '[' or '[<'
            if ch == '[':
                rlist, _, _ = select.select([sys.stdin], [], [], 0.03)
                if rlist:
                    rem = sys.stdin.read(1)
                    if rem == '<':
                        # Consume entire [<...;...;...m SGR sequence
                        while True:
                            rlist2, _, _ = select.select([sys.stdin], [], [], 0.02)
                            if not rlist2:
                                break
                            c_end = sys.stdin.read(1)
                            if c_end in ['m', 'M']:
                                break
                        return ('TIMEOUT', None)
                    else:
                        return ('KEY', '[' + rem)

            if ch == '\x1b':
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if not rlist:
                    return ('KEY', 'ESC')

                seq = ch
                while True:
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
                    if not rlist:
                        break
                    seq += sys.stdin.read(1)

                # Catch and suppress any XTerm SGR & X11 Mouse Sequence
                if re.search(r'(\x1b\[<|\x1b\[M)', seq):
                    sgr_matches = re.findall(r'\x1b\[<(\d+);(\d+);(\d+)([Mm])', seq)
                    if sgr_matches:
                        for b_str, c_str, r_str, m_type in sgr_matches:
                            try:
                                col, row = int(c_str), int(r_str)
                                payload = self.find_hitbox(row, col)
                                if payload:
                                    return ('HITBOX', payload)
                            except Exception:
                                pass
                    return ('TIMEOUT', None)

                if seq in ['\x1b', '\x1b\x1b']:
                    return ('KEY', 'ESC')
                if seq in ['\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D']:
                    return ('KEY', seq)

                # Suppress unhandled control sequences starting with ESC[
                if seq.startswith('\x1b['):
                    return ('TIMEOUT', None)

                return ('KEY', seq)

            elif ch in ['\x03', '\x1a']:  # Ctrl+C or Ctrl+Z -> Map to clean 'q' back/exit
                return ('KEY', 'q')
            else:
                return ('KEY', ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

TOUCH_ENGINE = TouchInputEngine()

def clear_screen():
    TOUCH_ENGINE.clear_hitboxes()
    os.system('clear' if os.name != 'nt' else 'cls')

def run_db_script(python_code: str) -> str:
    """Executes a Python database script inside the ModernWMS docker container."""
    proc = subprocess.run(
        ['docker', 'exec', '-i', CONTAINER, 'python3', '-'],
        input=python_code,
        capture_output=True,
        text=True
    )
    if proc.returncode != 0:
        return json.dumps({"error": proc.stderr.strip()})
    return proc.stdout.strip()

def log_audit_event(user_name: str, role: str, action: str, status: str, details: str = ""):
    """Logs security audit events with timestamp to /root/tui_audit.log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] USER:{user_name} | ROLE:{role} | ACTION:{action} | STATUS:{status}"
    if details:
        log_line += f" | DETAILS:{details}"
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except Exception:
        pass

# =============================================================================
# 🔐 AUTHENTICATION & DYNAMIC ROLE PERMISSION CONTROLLER
# =============================================================================

def fetch_user_permissions(user_role: str) -> dict:
    """Queries ModernWMS database to resolve exact menu permissions for user_role."""
    u_role_str = json.dumps(user_role)
    script = f'''
import sqlite3, json
conn = sqlite3.connect("{DB_PATH}")
c = conn.cursor()
role_name_in = {u_role_str}
role_row = c.execute("SELECT id FROM userrole WHERE LOWER(role_name) = LOWER(?)", (role_name_in,)).fetchone()
if not role_row:
    is_vo = role_name_in.lower() == 'viewonly' or 'view' in role_name_in.lower() or 'read' in role_name_in.lower()
    print(json.dumps({{
        "role_id": 0,
        "role_name": role_name_in,
        "menus": ["*"] if not is_vo else ["stockManagement", "baseModule", "stockAsn", "deliveryManagement", "commodityManagement", "supplier", "customer", "warehouseSetting", "ownerOfCargo", "freightSetting", "commodityCategorySetting"],
        "can_write": not is_vo,
        "is_admin": role_name_in.lower() == 'admin'
    }}))
    conn.close()
    exit(0)

role_id = role_row[0]
menu_rows = c.execute("""
    SELECT DISTINCT m.menu_name 
    FROM rolemenu rm 
    JOIN menu m ON rm.menu_id = m.id 
    WHERE rm.userrole_id = ?
""", (role_id,)).fetchall()
conn.close()
menus = [m[0] for m in menu_rows]
role_lower = role_name_in.lower()
is_viewonly = (role_lower == 'viewonly') or ('view' in role_lower) or ('read' in role_lower)
can_write = not is_viewonly
print(json.dumps({{
    "role_id": role_id,
    "role_name": role_name_in,
    "menus": menus,
    "can_write": can_write,
    "is_admin": role_lower == 'admin'
}}))
'''
    res = run_db_script(script)
    try:
        return json.loads(res)
    except Exception:
        return {"role_id": 0, "role_name": user_role, "menus": [], "can_write": False, "is_admin": False}

def has_menu_permission(session_user: dict, menu_name: str) -> bool:
    perms = session_user.get("permissions", {})
    if perms.get("is_admin") or "*" in perms.get("menus", []):
        return True
    return menu_name in perms.get("menus", [])

def has_any_menu_permission(session_user: dict, menu_names: list) -> bool:
    return any(has_menu_permission(session_user, m) for m in menu_names)

def check_write_permission(session_user: dict, action_name: str) -> bool:
    can_write = session_user.get("permissions", {}).get("can_write", True)
    if not can_write:
        print(f"\n{C_RED}❌ ACCESS DENIED: Role '{session_user.get('user_role')}' is restricted to ViewOnly. Cannot perform write action: {action_name}{CLR_RESET}")
        log_audit_event(session_user.get("user_name"), session_user.get("user_role"), action_name, "DENIED_VIEWONLY_RESTRICTION")
        press_enter_to_continue()
        return False
    return True

def authenticate_partdb_user(username_input: str, password_input: str) -> dict:
    if not os.path.exists(PARTDB_DB_PATH):
        return None
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        user_row = c.execute("""
            SELECT id, name, email, disabled, password, group_id
            FROM users 
            WHERE LOWER(name) = LOWER(?) OR LOWER(email) = LOWER(?)
        """, (username_input, username_input)).fetchone()
        conn.close()
        if not user_row:
            return None
        u_id, u_name, u_email, u_disabled, u_pwd_hash, group_id = user_row
        if u_disabled == 1:
            return {"disabled": True}
        if not u_pwd_hash:
            return None

        verified = False
        # Use container PHP password_verify engine
        proc = subprocess.run([
            'docker', 'exec', '-i', 'partdb', 'php', '-r',
            f'$h = \'{u_pwd_hash}\'; $p = \'{password_input}\'; echo password_verify($p, $h) ? "VALID" : "INVALID";'
        ], capture_output=True, text=True)

        if "VALID" in proc.stdout:
            verified = True
        else:
            try:
                import bcrypt
                if bcrypt.checkpw(password_input.encode('utf-8'), u_pwd_hash.encode('utf-8')):
                    verified = True
            except Exception:
                pass

        if verified:
            is_admin = (group_id == 1 or u_name.lower() == 'kcollins' or u_id in (1, 2))
            role_str = "PartDB Admin" if is_admin else "PartDB User"
            perms = fetch_user_permissions(role_str)
            log_audit_event(u_name, role_str, "LOGIN_PARTDB", "SUCCESS")
            return {
                "user_id": u_id,
                "user_name": u_name,
                "user_role": role_str,
                "auth_source": "PartDB",
                "permissions": perms
            }
    except Exception:
        pass
    return None

def authenticate_user(username_input: str, password_input: str) -> dict:
    pwd_json = json.dumps(password_input)
    u_name_json = json.dumps(username_input)
    script = f'''
import sqlite3, json, hashlib
conn = sqlite3.connect("{DB_PATH}")
c = conn.cursor()

pwd_in = {pwd_json}
u_in = {u_name_json}
pwd_md5 = hashlib.md5(pwd_in.encode('utf-8')).hexdigest()

user = c.execute("""
    SELECT u.id, u.user_num, u.user_name, u.user_role, u.is_valid
    FROM user u
    WHERE (LOWER(u.user_name) = LOWER(?) OR LOWER(u.user_num) = LOWER(?) OR u.id = ?)
      AND (u.auth_string = ? OR u.auth_string = ?)
    LIMIT 1
""", (u_in, u_in, u_in, pwd_in, pwd_md5)).fetchone()

if user:
    u_id, u_num, u_name, u_role, is_valid = user
    conn.close()
    print(json.dumps({{
        "user_id": u_id,
        "user_num": u_num,
        "user_name": u_name,
        "user_role": u_role,
        "is_valid": is_valid,
        "auth_source": "ModernWMS"
    }}))
    exit(0)

conn.close()
print(json.dumps({{}}))
'''
    res = run_db_script(script)
    try:
        wms_user = json.loads(res)
        if wms_user and wms_user.get("user_id"):
            if wms_user.get("is_valid") == 0 and wms_user.get("user_name") != "admin":
                log_audit_event(username_input, wms_user.get("user_role", "N/A"), "LOGIN", "FAILED_ACCOUNT_DISABLED")
                return {"disabled": True}
            u_role = wms_user.get("user_role", "User")
            perms = fetch_user_permissions(u_role)
            wms_user["permissions"] = perms
            log_audit_event(wms_user["user_name"], u_role, "LOGIN_MODERNWMS", "SUCCESS")
            return wms_user
    except Exception:
        pass

    pdb_user = authenticate_partdb_user(username_input, password_input)
    if pdb_user:
        return pdb_user

    log_audit_event(username_input, "N/A", "LOGIN", "FAILED_INVALID_CREDENTIALS")
    return None

def forced_password_change_prompt(src: str, username: str):
    """Forces user to set a new permanent password upon logging in with a temporary password."""
    while True:
        clear_screen()
        print(f"{C_YELLOW}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
        print(f"{C_YELLOW}│{CLR_RESET}  {ICO_LOCK} {CLR_BOLD}{C_WHITE}FIRST-TIME LOGIN: PASSWORD CHANGE REQUIRED{CLR_RESET}                       {C_YELLOW}│{CLR_RESET}")
        print(f"{C_YELLOW}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
        print(f"{C_YELLOW}│{CLR_RESET}  You are logged in with a temporary password on {C_CYAN}{src:<12}{CLR_RESET}.               {C_YELLOW}│{CLR_RESET}")
        print(f"{C_YELLOW}│{CLR_RESET}  For security compliance, you must choose a new permanent password.           {C_YELLOW}│{CLR_RESET}")
        print(f"{C_YELLOW}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")

        p1 = smart_input("🔑 Enter New Permanent Password:", allow_empty=False, is_password=True)
        if len(p1) < 4:
            print(f"{C_RED}❌ Password must be at least 4 characters long.{CLR_RESET}")
            time.sleep(1.5)
            continue
        p2 = smart_input("🔒 Confirm New Permanent Password:", allow_empty=False, is_password=True)
        if p1 != p2:
            print(f"{C_RED}❌ Passwords do not match! Please try again.{CLR_RESET}")
            time.sleep(1.5)
            continue

        ok, msg = user_manager.complete_forced_password_change(src, username, p1)
        if ok:
            print(f"\n{C_GREEN}{ICO_CHECK} {msg}{CLR_RESET}")
            time.sleep(1.2)
            break
        else:
            print(f"\n{C_RED}❌ {msg}{CLR_RESET}")
            time.sleep(2)

def login_prompt() -> dict:
    """Security login prompt interface requiring valid ModernWMS or PartDB credentials."""
    attempts = 0
    max_attempts = 5

    while attempts < max_attempts:
        clear_screen()
        print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
        print(f"{C_CYAN}│{CLR_RESET}  {ICO_SHIELD} {CLR_BOLD}{C_WHITE}ModernWMS & PartDB Terminal Suite - Secure Login{CLR_RESET}             {C_CYAN}│{CLR_RESET}")
        print(f"{C_CYAN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
        print(f"{C_CYAN}│{CLR_RESET} {C_YELLOW}Security Notice:{CLR_RESET} Login using ModernWMS or PartDB account credentials.        {C_CYAN}│{CLR_RESET}")
        print(f"{C_CYAN}│{CLR_RESET}  {BG_RED}{C_WHITE}{CLR_BOLD} [Q] 🚪 Quit / Exit Suite {CLR_RESET} {C_DIM}(Press Q / ESC / tap Quit anytime to exit){CLR_RESET}  {C_CYAN}│{CLR_RESET}")
        print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")

        # Register Quit hitbox on login screen (Line 5)
        TOUCH_ENGINE.register_hitbox(5, 5, 3, 26, "ACTION_EXIT")

        if attempts > 0:
            print(f"{C_RED}{ICO_CROSS} Authentication failed! ({attempts}/{max_attempts} attempts remaining){CLR_RESET}\n")

        username = smart_input("🔑 Username / User ID (or 'q' to Quit):", allow_empty=True)
        if username in ["__QUIT__", "__BACK__", "q", "Q", "quit", "exit", "ACTION_EXIT"]:
            print(f"\n{C_CYAN}Exiting ModernWMS & PartDB Hub. Goodbye!{CLR_RESET}\n")
            TOUCH_ENGINE.disable_mouse()
            sys.exit(0)

        if not username:
            continue

        password = smart_input("🔒 Password:", allow_empty=True, is_password=True)
        if password in ["__QUIT__", "ACTION_EXIT"]:
            print(f"\n{C_CYAN}Exiting ModernWMS & PartDB Hub. Goodbye!{CLR_RESET}\n")
            TOUCH_ENGINE.disable_mouse()
            sys.exit(0)

        if not password:
            continue

        print(f"\n{C_DIM}Authenticating against ModernWMS & PartDB security engines...{CLR_RESET}")
        user_info = authenticate_user(username, password)

        if user_info:
            if user_info.get("disabled"):
                print(f"\n{C_RED}{ICO_CROSS} Access Denied: Account '{username}' is disabled.{CLR_RESET}")
                time.sleep(2)
                TOUCH_ENGINE.disable_mouse()
                sys.exit(1)
            src = user_info.get("auth_source", "ModernWMS")
            u_name = user_info.get("user_name", username)

            # Enforce password reset on first login if temporary password
            if user_manager.check_must_change_password(src, u_name):
                forced_password_change_prompt(src, u_name)

            print(f"\n{C_GREEN}{ICO_CHECK} Login Successful! Welcome, {user_info['user_name']} [{src}] ({user_info['user_role']}).{CLR_RESET}")
            time.sleep(0.8)
            return user_info

        attempts += 1

    print(f"\n{C_RED}❌ Maximum failed login attempts exceeded. Session terminated.{CLR_RESET}")
    TOUCH_ENGINE.disable_mouse()
    sys.exit(1)

# =============================================================================
# 🎨 TUI RENDERER, TAB NAVIGATION & TOUCH INTERACTION DOCK
# =============================================================================

AVAILABLE_TABS = [
    ("dashboard", "1", "📊", "Overview"),
    ("partdb", "2", "🔩", "PartDB Hub"),
    ("scripts", "3", "⚡", "Script Hub"),
    ("asn", "4", "📦", "Inbound ASN"),
    ("warehouse_ops", "5", "🏭", "Warehouse Ops"),
    ("stock_lookup", "6", "🔍", "Inventory"),
    ("master_data", "7", "📋", "Master Data"),
    ("user_mgmt", "8", "👤", "Users"),
    ("delivery", "9", "🚚", "Outbound"),
    ("docker", "d", "🐳", "Containers")
]

def draw_header(session_user: dict, title: str, active_tab_key: str = None):
    """Renders top branding header, status badges, touch action bar, and Tab Bar."""
    clear_screen()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    u_name = session_user.get("user_name", "Unknown")
    u_role = session_user.get("user_role", "User")
    u_src  = session_user.get("auth_source", "WMS")
    can_write = session_user.get("permissions", {}).get("can_write", True)
    is_view_role = (u_role.lower() == "viewonly") or ("view" in u_role.lower()) or ("read" in u_role.lower())

    if is_view_role or not can_write:
        badge = f"{BG_YELLOW}{C_WHITE}{CLR_BOLD} {ICO_EYE} VIEW-ONLY {CLR_RESET}"
    elif u_role.lower() in ["admin", "partdb admin"]:
        badge = f"{BG_BLUE}{C_WHITE}{CLR_BOLD} ⚡ ADMIN {CLR_RESET}"
    else:
        badge = f"{BG_GREEN}{C_WHITE}{CLR_BOLD} 📦 OPERATOR {CLR_RESET}"

    # Top Brand Header (Lines 1-3)
    print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET} {CLR_BOLD}{C_WHITE}ModernWMS & PartDB Touch Control Suite{CLR_RESET}               {C_DIM}{now_str}{CLR_RESET} {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET} {C_DIM}User:{CLR_RESET} {C_YELLOW}{u_name:<10}{CLR_RESET} {C_DIM}Source:{CLR_RESET} {C_PURPLE}{u_src:<8}{CLR_RESET} {C_DIM}Role:{CLR_RESET} {C_WHITE}{u_role:<10}{CLR_RESET} {badge} {C_CYAN}│{CLR_RESET}")

    # Top Touch Quick Bar (Line 4)
    # Register hitboxes for Quick Actions
    # [ 🔙 Q: BACK ]  [ ↺ U: UNDO ]  [ ➕ +: QUICK ADD ]  [ 🎨 T: THEME ]  [ 🔒 L: LOCK ]  [ 🚪 Q: EXIT ]
    act_bar = f" {BG_DARK}{C_CYAN} {ICO_BACK} Q:BACK {CLR_RESET} {BG_DARK}{C_YELLOW} {ICO_UNDO} U:UNDO {CLR_RESET} {BG_DARK}{C_GREEN} {ICO_ADD} +:ADD {CLR_RESET} {BG_DARK}{C_PURPLE} {ICO_THEME} T:THEME {CLR_RESET} {BG_DARK}{C_WHITE} {ICO_LOCK} L:LOCK {CLR_RESET} {BG_DARK}{C_RED} 🚪 Q:EXIT {CLR_RESET}"
    print(f"{C_CYAN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}{act_bar}  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}")

    # Register top action hitboxes (Line 5)
    TOUCH_ENGINE.register_hitbox(5, 5, 2, 12, "ACTION_BACK")
    TOUCH_ENGINE.register_hitbox(5, 5, 14, 24, "ACTION_UNDO")
    TOUCH_ENGINE.register_hitbox(5, 5, 26, 35, "ACTION_ADD")
    TOUCH_ENGINE.register_hitbox(5, 5, 37, 47, "ACTION_THEME")
    TOUCH_ENGINE.register_hitbox(5, 5, 49, 58, "ACTION_LOCK")
    TOUCH_ENGINE.register_hitbox(5, 5, 60, 72, "ACTION_EXIT")

    # Render Visual Pill Tab Navigation Bar (Lines 7-8)
    draw_tab_bar(session_user, active_tab_key)

    # Active Toast Alert Banner
    if TOUCH_ENGINE.active_toast and (time.time() - TOUCH_ENGINE.toast_time < 5.0):
        t_color = C_RED if TOUCH_ENGINE.toast_is_error else C_GREEN
        print(f" {t_color}{CLR_BOLD}>> TOAST: {TOUCH_ENGINE.active_toast}{CLR_RESET}\n")

    print(f"{C_BOLD}{C_PURPLE} ▶ {title.upper()}{CLR_RESET}\n")

def draw_tab_bar(session_user: dict, active_tab_key: str = None):
    """Renders modern visual pill cards representing navigation tabs and registers touch hitboxes."""
    tab_pills = []
    col_cursor = 2

    for key, num, icon, label in AVAILABLE_TABS:
        if key not in ["dashboard", "partdb", "scripts"] and not is_module_allowed(session_user, key):
            continue

        label_txt = f"[{num}] {icon} {label}"
        pill_len = len(label_txt) + 2

        if active_tab_key and key == active_tab_key:
            pill = f"{BG_CYAN}{C_WHITE}{CLR_BOLD} {label_txt} {CLR_RESET}"
        else:
            pill = f"{BG_DARK}{C_CYAN} {label_txt} {CLR_RESET}"

        tab_pills.append(pill)
        # Register hitboxes across rows 6, 7, and 8 with generous touch padding
        for r_row in [6, 7, 8]:
            TOUCH_ENGINE.register_hitbox(r_row, r_row, max(1, col_cursor - 1), col_cursor + pill_len + 1, f"TAB_{key}")
        col_cursor += pill_len + 1

    print(f" " + " ".join(tab_pills))
    print(f"{C_CYAN}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

def draw_footer():
    """Renders touch fast-dock footer."""
    print(f"\n{C_CYAN}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")
    print(f"{C_DIM} Touch Dock: [Q/B] Back | [U] Undo | [+] Quick Add | [T] Theme | [L] Lock | [Q] Exit{CLR_RESET}")

def press_enter_to_continue():
    if sys.stdin.isatty():
        smart_input("Press [ENTER] or tap Back to continue...", allow_empty=True)

def is_module_allowed(session_user: dict, module_key: str) -> bool:
    perms = session_user.get("permissions", {})
    if perms.get("is_admin"):
        return True
    if module_key in ["partdb", "scripts"]:
        return True

    key_map = {
        "asn": ["stockAsn"],
        "warehouse_ops": ["warehouseProcessing", "warehouseMove", "warehouseFreeze", "warehouseAdjust", "warehouseTaking"],
        "stock_lookup": ["stockManagement"],
        "master_data": ["baseModule", "commodityManagement", "supplier", "customer", "warehouseSetting", "ownerOfCargo", "freightSetting", "commodityCategorySetting"],
        "user_mgmt": ["userManagement", "userRoleSetting", "roleMenu"],
        "delivery": ["deliveryManagement"],
        "docker": []
    }

    req_menus = key_map.get(module_key, [])
    if not req_menus:
        return False
    return has_any_menu_permission(session_user, req_menus)

# =============================================================================
# 📱 SMART INPUT ENGINE & TOUCH NUMPAD OVERLAY
# =============================================================================

def draw_numpad_overlay(y_start: int):
    """Renders an on-screen Touch NumPad overlay for tablets."""
    print(f"\n{C_CYAN}╭─────────────────────────╮{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {CLR_BOLD}📱 TOUCH NUMPAD OPERATOR{CLR_RESET} {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}├─────────────────────────┤{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {BG_DARK}{C_WHITE} [1] {CLR_RESET}  {BG_DARK}{C_WHITE} [2] {CLR_RESET}  {BG_DARK}{C_WHITE} [3] {CLR_RESET}  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {BG_DARK}{C_WHITE} [4] {CLR_RESET}  {BG_DARK}{C_WHITE} [5] {CLR_RESET}  {BG_DARK}{C_WHITE} [6] {CLR_RESET}  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {BG_DARK}{C_WHITE} [7] {CLR_RESET}  {BG_DARK}{C_WHITE} [8] {CLR_RESET}  {BG_DARK}{C_WHITE} [9] {CLR_RESET}  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {BG_DARK}{C_RED} [C] {CLR_RESET}  {BG_DARK}{C_WHITE} [0] {CLR_RESET}  {BG_GREEN}{C_WHITE} [✔] {CLR_RESET}  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}╰─────────────────────────╯{CLR_RESET}")

    # Register NumPad hitboxes
    TOUCH_ENGINE.register_hitbox(y_start + 3, y_start + 3, 5, 9, "NUM_1")
    TOUCH_ENGINE.register_hitbox(y_start + 3, y_start + 3, 12, 16, "NUM_2")
    TOUCH_ENGINE.register_hitbox(y_start + 3, y_start + 3, 19, 23, "NUM_3")

    TOUCH_ENGINE.register_hitbox(y_start + 4, y_start + 4, 5, 9, "NUM_4")
    TOUCH_ENGINE.register_hitbox(y_start + 4, y_start + 4, 12, 16, "NUM_5")
    TOUCH_ENGINE.register_hitbox(y_start + 4, y_start + 4, 19, 23, "NUM_6")

    TOUCH_ENGINE.register_hitbox(y_start + 5, y_start + 5, 5, 9, "NUM_7")
    TOUCH_ENGINE.register_hitbox(y_start + 5, y_start + 5, 12, 16, "NUM_8")
    TOUCH_ENGINE.register_hitbox(y_start + 5, y_start + 5, 19, 23, "NUM_9")

    TOUCH_ENGINE.register_hitbox(y_start + 6, y_start + 6, 5, 9, "NUM_CLEAR")
    TOUCH_ENGINE.register_hitbox(y_start + 6, y_start + 6, 12, 16, "NUM_0")
    TOUCH_ENGINE.register_hitbox(y_start + 6, y_start + 6, 19, 23, "NUM_CONFIRM")

def smart_input(prompt: str, allow_empty: bool = True, default: str = "", numpad: bool = False, is_password: bool = False, session_user: dict = None) -> str:
    """Touch & Keypress Input Handler. Replaces standard input() calls.
    Returns: String value, '__BACK__', '__QUIT__', or '__TAB_xyz__'.
    """
    sys.stdout.write(f"\r{C_BOLD}{C_CYAN}{prompt}{CLR_RESET} ")
    sys.stdout.flush()

    buf = ""

    if numpad:
        draw_numpad_overlay(15)

    while True:
        event_type, val = TOUCH_ENGINE.read_char_or_touch()

        if event_type == 'HITBOX':
            payload = val
            if payload in ["ACTION_BACK", "NAV_BACK"]:
                return "__BACK__"
            elif payload == "ACTION_EXIT":
                return "__QUIT__"
            elif payload == "ACTION_UNDO":
                ok, msg = TOUCH_ENGINE.undo_stack.undo()
                TOUCH_ENGINE.show_toast(msg, is_error=not ok)
                print(f"\n{C_YELLOW}{msg}{CLR_RESET}")
                return "__BACK__"
            elif payload == "ACTION_ADD":
                if session_user:
                    show_quick_add_drawer(session_user)
                    return "__BACK__"
            elif payload == "ACTION_THEME":
                select_theme_modal()
                return "__BACK__"
            elif payload.startswith("TAB_"):
                return f"__{payload}__"
            elif payload.startswith("NUM_"):
                n_key = payload[4:]
                if n_key == "CLEAR":
                    buf = ""
                    sys.stdout.write(f"\r{C_BOLD}{C_CYAN}{prompt}{CLR_RESET} \033[K")
                    sys.stdout.flush()
                elif n_key == "CONFIRM":
                    print()
                    return buf if buf else default
                else:
                    buf += n_key
                    sys.stdout.write("*" if is_password else n_key)
                    sys.stdout.flush()
            elif payload.startswith("SELECT_ROW_") or payload.startswith("INSPECT_PART_") or payload.startswith("OPTION_") or payload.startswith("SELECT_THEME_"):
                return payload

        elif event_type == 'KEY':
            ch = val
            if ch in ['\r', '\n']:
                print()
                return buf if buf else default
            elif ch in ['\x7f', '\x08']:  # Backspace
                if len(buf) > 0:
                    buf = buf[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif ch in ['q', 'Q', 'b', 'B', 'ESC']:
                if not buf and not is_password:
                    print()
                    return "__QUIT__" if ch in ['q', 'Q'] else "__BACK__"
                else:
                    buf += ch
                    sys.stdout.write("*" if is_password else ch)
                    sys.stdout.flush()
            elif ch in ['u', 'U'] and not buf and not is_password:
                ok, msg = TOUCH_ENGINE.undo_stack.undo()
                TOUCH_ENGINE.show_toast(msg, is_error=not ok)
                print(f"\n{C_YELLOW}{msg}{CLR_RESET}")
                return "__BACK__"
            elif ch == '+' and not buf and not is_password and session_user:
                show_quick_add_drawer(session_user)
                return "__BACK__"
            elif ch in ['t', 'T'] and not buf and not is_password:
                select_theme_modal()
                return "__BACK__"
            else:
                # Sanitize input: Filter out non-printable chars or ANSI escape fragments
                clean_chars = "".join(c for c in ch if c.isprintable() and ord(c) >= 32)
                # Discard any SGR mouse coordinate noise e.g. [<0;46;15m
                if clean_chars and not clean_chars.startswith('[<') and not ('<0;' in clean_chars):
                    buf += clean_chars
                    sys.stdout.write("*" if is_password else clean_chars)
                    sys.stdout.flush()

def select_theme_modal():
    """Visual theme picker modal allowing quick selection across all available themes."""
    global ACTIVE_THEME_NAME
    clear_screen()
    print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {ICO_THEME} {CLR_BOLD}{C_WHITE}VISUAL THEME SELECTOR MODAL{CLR_RESET}                                      {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")

    theme_keys = list(THEMES.keys())
    for idx, t_key in enumerate(theme_keys, 1):
        active_mark = f"{C_GREEN}✔ (Active){CLR_RESET}" if t_key == ACTIVE_THEME_NAME else ""
        label = t_key.replace("_", " ").title()
        y_line = 3 + idx
        print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[{idx}]{CLR_RESET} {label:<28} {active_mark:<20} {C_CYAN}│{CLR_RESET}")
        TOUCH_ENGINE.register_hitbox(y_line, y_line, 3, 70, f"SELECT_THEME_{t_key}")

    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[Q]{CLR_RESET} 🔙 Return to View                                              {C_CYAN}│{CLR_RESET}")
    y_q = 4 + len(theme_keys)
    TOUCH_ENGINE.register_hitbox(y_q, y_q, 3, 70, "ACTION_BACK")
    print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")

    choice = smart_input("Select Theme [1-8, Q]:", allow_empty=True)
    if choice.startswith("SELECT_THEME_"):
        new_t = choice.replace("SELECT_THEME_", "")
        if new_t in THEMES:
            ACTIVE_THEME_NAME = new_t
            update_color_globals()
            TOUCH_ENGINE.show_toast(f"Theme switched to: {ACTIVE_THEME_NAME.upper()}")
    elif choice in ["1", "2", "3", "4", "5", "6", "7", "8"]:
        try:
            sel_idx = int(choice) - 1
            if 0 <= sel_idx < len(theme_keys):
                ACTIVE_THEME_NAME = theme_keys[sel_idx]
                update_color_globals()
                TOUCH_ENGINE.show_toast(f"Theme switched to: {ACTIVE_THEME_NAME.upper()}")
        except ValueError:
            pass

def toggle_theme():
    select_theme_modal()

# =============================================================================
# ➕ TOUCH QUICK ADD OVERLAY DRAWER
# =============================================================================

def show_quick_add_drawer(session_user: dict):
    """Floating touch-friendly drawer overlay for 1-tap quick actions from anywhere."""
    clear_screen()
    print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {ICO_ADD} {CLR_BOLD}{C_WHITE}TOUCH QUICK ADD OVERLAY DRAWER{CLR_RESET}                                  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[1]{CLR_RESET} 🔩 Quick PartDB Component Creation                                {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[2]{CLR_RESET} 📦 Quick Inbound Stock Receipt (Notice on Arrival / ASN)            {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[3]{CLR_RESET} 🏭 Quick Stock Quantity Adjustment                                {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[4]{CLR_RESET} 📋 Quick Master Data Entry (Supplier / Customer)                  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}[Q]{CLR_RESET} 🔙 Return to View                                                  {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")

    TOUCH_ENGINE.register_hitbox(4, 4, 3, 70, "OPTION_1")
    TOUCH_ENGINE.register_hitbox(5, 5, 3, 70, "OPTION_2")
    TOUCH_ENGINE.register_hitbox(6, 6, 3, 70, "OPTION_3")
    TOUCH_ENGINE.register_hitbox(7, 7, 3, 70, "OPTION_4")
    TOUCH_ENGINE.register_hitbox(8, 8, 3, 70, "ACTION_BACK")

    choice = smart_input("Select Quick Action [1-4, Q]:", allow_empty=True, session_user=session_user)
    if choice in ["1", "OPTION_1"]:
        module_partdb_create(session_user)
    elif choice in ["2", "OPTION_2"]:
        module_receive_stock(session_user)
    elif choice in ["3", "OPTION_3"]:
        module_partdb_stock_adjust(session_user)
    elif choice in ["4", "OPTION_4"]:
        module_master_data(session_user)

# =============================================================================
# 🔍 RECORD INSPECTOR MODAL
# =============================================================================

def inspect_record_modal(record_dict: dict, title: str = "Record Details"):
    """Displays an interactive modal card inspecting all attributes of a record."""
    clear_screen()
    print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
    print(f"{C_CYAN}│{CLR_RESET}  {ICO_SEARCH} {CLR_BOLD}{C_WHITE}INSPECTOR CARD: {title.upper()}{CLR_RESET}                                   {C_CYAN}│{CLR_RESET}")
    print(f"{C_CYAN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")

    for key, val in record_dict.items():
        val_str = str(val) if val is not None else "N/A"
        print(f"{C_CYAN}│{CLR_RESET}  {C_YELLOW}{key:<25}:{CLR_RESET} {C_WHITE}{val_str:<47}{CLR_RESET} {C_CYAN}│{CLR_RESET}")

    print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}")
    press_enter_to_continue()

# =============================================================================
# 📊 TASK MODULE: EXECUTIVE KPI DASHBOARD & MULTI-ECOLOGY OVERVIEW
# =============================================================================

def fetch_dashboard_metrics() -> dict:
    """Queries both ModernWMS and PartDB databases to collect system metrics."""
    data = {}
    wms_script = f'''
import sqlite3, json
conn = sqlite3.connect("{DB_PATH}")
c = conn.cursor()

spu_cnt = c.execute("SELECT COUNT(*) FROM spu WHERE is_valid=1").fetchone()[0]
stock_sum = c.execute("SELECT COALESCE(SUM(qty), 0) FROM stock").fetchone()[0]
frozen_cnt = c.execute("SELECT COUNT(*) FROM stock WHERE is_freeze=1 AND qty>0").fetchone()[0]
asn_cnt = c.execute("SELECT COUNT(*) FROM asn WHERE is_valid=1").fetchone()[0]
dispatch_cnt = c.execute("SELECT COUNT(*) FROM dispatchlist WHERE is_valid=1").fetchone()[0]
user_cnt = c.execute("SELECT COUNT(*) FROM user").fetchone()[0]
supplier_cnt = c.execute("SELECT COUNT(*) FROM supplier WHERE is_valid=1").fetchone()[0]
customer_cnt = c.execute("SELECT COUNT(*) FROM customer WHERE is_valid=1").fetchone()[0]

low_stock_cnt = c.execute("SELECT COUNT(*) FROM stock WHERE qty <= 5").fetchone()[0]
conn.close()

print(json.dumps({{
    "spu_cnt": spu_cnt,
    "stock_sum": stock_sum,
    "frozen_cnt": frozen_cnt,
    "asn_cnt": asn_cnt,
    "dispatch_cnt": dispatch_cnt,
    "user_cnt": user_cnt,
    "supplier_cnt": supplier_cnt,
    "customer_cnt": customer_cnt,
    "low_stock_cnt": low_stock_cnt
}}))
'''
    res = run_db_script(wms_script)
    try:
        data.update(json.loads(res))
    except Exception:
        pass

    if os.path.exists(PARTDB_DB_PATH):
        try:
            conn = sqlite3.connect(PARTDB_DB_PATH)
            c = conn.cursor()
            p_cnt = c.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
            cat_cnt = c.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
            loc_cnt = c.execute("SELECT COUNT(*) FROM storelocations").fetchone()[0]
            lot_sum = c.execute("SELECT COALESCE(SUM(amount), 0) FROM part_lots").fetchone()[0]
            conn.close()

            data["partdb_parts_cnt"] = p_cnt
            data["partdb_cats_cnt"]  = cat_cnt
            data["partdb_locs_cnt"]  = loc_cnt
            data["partdb_stock_sum"] = lot_sum
        except Exception:
            pass

    proc = subprocess.run(['docker', 'inspect', '-f', '{{.State.Status}}', CONTAINER], capture_output=True, text=True)
    container_status = proc.stdout.strip().upper() if proc.returncode == 0 else "OFFLINE"
    data['container_status'] = container_status
    return data

def render_sparkline(val: float, max_val: float = 100.0, width: int = 10) -> str:
    """Renders a dynamic Unicode visual progress sparkline."""
    if max_val <= 0:
        max_val = 100.0
    ratio = min(1.0, max(0.0, val / max_val))
    filled = int(round(ratio * width))
    bar = "█" * filled + "░" * (width - filled)
    pct = int(ratio * 100)
    return f"[{bar} {pct:>3}%]"

def module_overview_dashboard(session_user: dict):
    draw_header(session_user, "Executive KPI Dashboard & Multi-Ecology Overview", active_tab_key="dashboard")
    print(f"{C_DIM}Fetching live metrics from ModernWMS & PartDB databases...{CLR_RESET}\n")

    data = fetch_dashboard_metrics()
    spu_cnt = data.get("spu_cnt", 0)
    stock_sum = data.get("stock_sum", 0)
    frozen_cnt = data.get("frozen_cnt", 0)
    asn_cnt = data.get("asn_cnt", 0)
    dispatch_cnt = data.get("dispatch_cnt", 0)
    user_cnt = data.get("user_cnt", 0)
    low_stock_cnt = data.get("low_stock_cnt", 0)
    container_status = data.get("container_status", "UNKNOWN")

    pdb_parts = data.get("partdb_parts_cnt", 0)
    pdb_cats  = data.get("partdb_cats_cnt", 0)
    pdb_locs  = data.get("partdb_locs_cnt", 0)
    pdb_stock = data.get("partdb_stock_sum", 0)

    c_color = C_GREEN if container_status in ["RUNNING", "UP"] else C_RED
    c_bg = BG_GREEN if container_status in ["RUNNING", "UP"] else BG_RED

    spark_wms = render_sparkline(stock_sum, 5000.0)
    spark_pdb = render_sparkline(pdb_stock, 5000.0)

    print(f"{C_CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}   {ICO_CHART} {CLR_BOLD}{C_WHITE}MODERNWMS & PARTDB DUAL KPI ANALYTICS DASHBOARD{CLR_RESET}                 {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════════════╣{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}  📦 WMS Total SPUs       : {C_YELLOW}{spu_cnt:<8}{CLR_RESET} │ 🏭 WMS Stock {spark_wms} {C_GREEN}{stock_sum:<5} pcs{CLR_RESET} {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}  ❄️ WMS QA Hold SKUs     : {C_RED}{frozen_cnt:<8}{CLR_RESET} │ 🚚 WMS Dispatches      : {C_BLUE}{dispatch_cnt:<8}{CLR_RESET}       {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}  📥 WMS Inbound ASNs     : {C_PURPLE}{asn_cnt:<8}{CLR_RESET} │ 👤 WMS Registered Users: {C_WHITE}{user_cnt:<8}{CLR_RESET}       {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════════════╣{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}  🔩 PartDB Total Parts   : {C_CYAN}{pdb_parts:<8}{CLR_RESET} │ 📊 PartDB Stock {spark_pdb} {C_GREEN}{pdb_stock:<5} pcs{CLR_RESET}{C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}║{CLR_RESET}  🏷️ PartDB Categories    : {C_YELLOW}{pdb_cats:<8}{CLR_RESET} │ 📍 PartDB Storage Locs : {C_WHITE}{pdb_locs:<8}{CLR_RESET}       {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════════════╣{CLR_RESET}")

    if low_stock_cnt > 0:
        print(f"{C_CYAN}║{CLR_RESET}  {ICO_ALERT} {C_RED}{CLR_BOLD}LOW STOCK ALERT:{CLR_RESET} {C_YELLOW}{low_stock_cnt} item(s) have inventory balance <= 5 pcs{CLR_RESET}       {C_CYAN}║{CLR_RESET}")
        print(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════════════╣{CLR_RESET}")

    print(f"{C_CYAN}║{CLR_RESET}  🐳 Container Status     : {c_bg}{C_WHITE}{CLR_BOLD} {container_status} {CLR_RESET} {c_color}(Port 80 / 8081 / 8082 Active){CLR_RESET}    {C_CYAN}║{CLR_RESET}")
    print(f"{C_CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{CLR_RESET}")

    # Register Metric Card Touch Hitboxes (Line 15 & 19)
    TOUCH_ENGINE.register_hitbox(15, 15, 3, 30, "TAB_stock_lookup")
    TOUCH_ENGINE.register_hitbox(19, 19, 3, 30, "TAB_partdb")

    draw_footer()
    press_enter_to_continue()

# =============================================================================
# 🔩 TASK MODULE: PARTDB TERMINAL PART CREATOR & INVENTORY MANAGER
# =============================================================================

def get_partdb_categories():
    if not os.path.exists(PARTDB_DB_PATH): return []
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        rows = c.execute("SELECT id, name FROM categories ORDER BY name ASC").fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def get_partdb_storelocations():
    if not os.path.exists(PARTDB_DB_PATH): return []
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        rows = c.execute("SELECT id, name FROM storelocations ORDER BY name ASC").fetchall()
        conn.close()
        return rows
    except Exception:
        return []

def module_partdb_browse(session_user: dict):
    """Searches and lists PartDB parts with category, location, and touch row selection."""
    draw_header(session_user, "PartDB Inventory Directory", active_tab_key="partdb")
    search = smart_input("Search PartDB (Name, MPN, Cat) [Enter for all]:", allow_empty=True, session_user=session_user)
    if search in ["__BACK__", "__QUIT__"] or search.startswith("__TAB_"):
        return

    if not os.path.exists(PARTDB_DB_PATH):
        print(f"{C_RED}❌ PartDB Database not found at {PARTDB_DB_PATH}{CLR_RESET}")
        press_enter_to_continue()
        return

    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        query = """
            SELECT p.id, p.name, p.manufacturer_product_number, c.name as category, 
                   COALESCE(SUM(pl.amount), 0) as stock_qty, sl.name as location, p.description
            FROM parts p
            LEFT JOIN categories c ON p.id_category = c.id
            LEFT JOIN part_lots pl ON pl.id_part = p.id
            LEFT JOIN storelocations sl ON pl.id_store_location = sl.id
            WHERE (? = '' OR p.name LIKE ? OR p.manufacturer_product_number LIKE ? OR c.name LIKE ? OR p.description LIKE ?)
            GROUP BY p.id
            ORDER BY p.id DESC
            LIMIT 50
        """
        s_pattern = f"%{search}%"
        rows = c.execute(query, (search, s_pattern, s_pattern, s_pattern, s_pattern)).fetchall()
        conn.close()

        print(f"\n{C_BOLD}{C_WHITE}{'ID':<6} {'Part Name':<30} {'MPN/IPN':<15} {'Category':<15} {'Stock':<10} {'Location':<12}{CLR_RESET}")
        print(f"{C_CYAN}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")

        if not rows:
            print(f"{C_YELLOW}No matching PartDB components found.{CLR_RESET}")
        else:
            y_row_start = 14
            for idx, r in enumerate(rows):
                p_id, name, mpn, cat, qty, loc, desc = r
                name_fmt = (name[:28] + "..") if len(name) > 30 else name
                mpn_fmt  = (mpn[:13] + "..") if mpn and len(mpn) > 15 else (mpn or "N/A")
                cat_fmt  = (cat[:13] + "..") if cat and len(cat) > 15 else (cat or "N/A")
                loc_fmt  = (loc[:10] + "..") if loc and len(loc) > 12 else (loc or "Main")
                q_color  = C_GREEN if qty > 5 else (C_YELLOW if qty > 0 else C_RED)

                y_curr = y_row_start + idx
                TOUCH_ENGINE.register_hitbox(y_curr, y_curr, 1, 80, f"INSPECT_PART_{p_id}")
                print(f"{C_CYAN}#{p_id:<5}{CLR_RESET} {C_WHITE}{name_fmt:<30}{CLR_RESET} {C_GRAY}{mpn_fmt:<15}{CLR_RESET} {C_PURPLE}{cat_fmt:<15}{CLR_RESET} {q_color}{qty:<10.0f}{CLR_RESET} {C_BLUE}{loc_fmt:<12}{CLR_RESET}")

        print(f"\n{C_DIM}Tap any row on screen or enter Part ID # to inspect details, or [Q] to return.{CLR_RESET}")
        choice = smart_input("Inspect Part ID #:", allow_empty=True, numpad=True, session_user=session_user)

        target_id = None
        if choice.startswith("INSPECT_PART_"):
            target_id = int(choice.replace("INSPECT_PART_", ""))
        elif choice.isdigit():
            target_id = int(choice)

        if target_id:
            conn = sqlite3.connect(PARTDB_DB_PATH)
            c = conn.cursor()
            p_data = c.execute("""
                SELECT p.id, p.name, p.description, p.comment, p.manufacturer_product_number, p.minamount,
                       c.name as category, sl.name as location, COALESCE(SUM(pl.amount), 0) as total_stock
                FROM parts p
                LEFT JOIN categories c ON p.id_category = c.id
                LEFT JOIN part_lots pl ON pl.id_part = p.id
                LEFT JOIN storelocations sl ON pl.id_store_location = sl.id
                WHERE p.id = ?
                GROUP BY p.id
            """, (target_id,)).fetchone()
            conn.close()
            if p_data:
                inspect_record_modal({
                    "Part ID": p_data[0],
                    "Part Name": p_data[1],
                    "Description": p_data[2],
                    "Comment": p_data[3],
                    "Part Number (MPN/IPN)": p_data[4],
                    "Min Amount": p_data[5],
                    "Category": p_data[6],
                    "Storage Location": p_data[7],
                    "Current In-Stock Qty": p_data[8]
                }, title=f"PartDB Item #{p_data[0]} - {p_data[1]}")
    except Exception as e:
        print(f"{C_RED}❌ Error reading PartDB: {e}{CLR_RESET}")
        press_enter_to_continue()

def module_partdb_create(session_user: dict):
    """Wizard to add a new component/part directly into PartDB database with Undo support."""
    if not check_write_permission(session_user, "Create PartDB Component"):
        return

    draw_header(session_user, "Terminal PartDB Part Creator Wizard", active_tab_key="partdb")
    print(f"{C_WHITE}Enter component details below (Tap [Q] or Back anytime to cancel):{CLR_RESET}\n")

    name = smart_input("Part Name (required):", allow_empty=False, session_user=session_user)
    if name in ["__BACK__", "__QUIT__"] or not name:
        return

    description = smart_input("Description:", allow_empty=True, session_user=session_user)
    if description == "__BACK__": return
    mpn = smart_input("Manufacturer Part Number (MPN / IPN / SKU):", allow_empty=True, session_user=session_user)
    if mpn == "__BACK__": return

    # Category Selection
    cats = get_partdb_categories()
    print(f"\n{C_YELLOW}Available Categories:{CLR_RESET}")
    for idx, (c_id, c_name) in enumerate(cats[:10], start=1):
        print(f"  [{idx}] {c_name}")
        TOUCH_ENGINE.register_hitbox(16 + idx, 16 + idx, 2, 40, f"OPTION_CAT_{c_id}")

    c_choice = smart_input("Select Category [1-10, or type name]:", allow_empty=True, numpad=True, session_user=session_user)
    if c_choice == "__BACK__": return

    cat_id = 7
    if c_choice.startswith("OPTION_CAT_"):
        cat_id = int(c_choice.replace("OPTION_CAT_", ""))
    elif c_choice.isdigit() and 1 <= int(c_choice) <= len(cats[:10]):
        cat_id = cats[int(c_choice) - 1][0]
    elif c_choice:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        c_row = c.execute("SELECT id FROM categories WHERE LOWER(name) = LOWER(?)", (c_choice,)).fetchone()
        if c_row:
            cat_id = c_row[0]
        else:
            c.execute("INSERT INTO categories (name, parent_id) VALUES (?, NULL)", (c_choice,))
            cat_id = c.lastrowid
            conn.commit()
        conn.close()

    initial_qty_str = smart_input("Initial In-Stock Quantity (pcs) [Default 0]:", allow_empty=True, numpad=True, session_user=session_user)
    if initial_qty_str == "__BACK__": return
    try:
        initial_qty = float(initial_qty_str) if initial_qty_str else 0.0
    except ValueError:
        initial_qty = 0.0

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO parts (id_category, datetime_added, name, last_modified, needs_review, tags, 
                               description, comment, visible, favorite, minamount, manufacturer_product_url, 
                               manufacturer_product_number, order_quantity, manual_order, ipn)
            VALUES (?, ?, ?, ?, 0, '', ?, '', 1, 0, 0, '', ?, 0, 0, ?)
        """, (cat_id, now_str, name, now_str, description, mpn, mpn if mpn else None))
        part_id = c.lastrowid

        if initial_qty > 0:
            c.execute("""
                INSERT INTO part_lots (id_store_location, id_part, description, comment, instock_unknown, 
                                       amount, needs_refill, last_modified, datetime_added)
                VALUES (1, ?, 'Initial stock setup', '', 0, ?, 0, ?, ?)
            """, (part_id, initial_qty, now_str, now_str))

        conn.commit()
        conn.close()

        # Register Undo Handler
        def undo_create():
            c2 = sqlite3.connect(PARTDB_DB_PATH)
            c2.execute("DELETE FROM part_lots WHERE id_part = ?", (part_id,))
            c2.execute("DELETE FROM parts WHERE id = ?", (part_id,))
            c2.commit()
            c2.close()

        TOUCH_ENGINE.undo_stack.push(f"Created PartDB Part #{part_id} ({name})", undo_create)

        print(f"\n{C_GREEN}╭────────────────────────────────────────────────────────────╮{CLR_RESET}")
        print(f"{C_GREEN}│ {ICO_CHECK} PartDB Component Created Successfully!                      │{CLR_RESET}")
        print(f"{C_GREEN}├────────────────────────────────────────────────────────────┤{CLR_RESET}")
        print(f"  Part ID #:           {C_YELLOW}#{part_id}{CLR_RESET}")
        print(f"  Part Name:           {C_WHITE}{name}{CLR_RESET}")
        print(f"  Initial Stock:       {C_BOLD}{C_GREEN}{initial_qty} pcs{CLR_RESET}")
        print(f"{C_GREEN}╰────────────────────────────────────────────────────────────╯{CLR_RESET}")

        log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "CREATE_PARTDB_PART", "SUCCESS", f"PART_ID:#{part_id}, NAME:{name}")
        TOUCH_ENGINE.show_toast(f"Component #{part_id} Created! Tap [Undo] to revert.")

    except Exception as e:
        print(f"{C_RED}❌ Error creating component in PartDB: {e}{CLR_RESET}")

    press_enter_to_continue()

def module_partdb_stock_adjust(session_user: dict):
    """Adjusts or receives stock for a PartDB component with Undo support."""
    if not check_write_permission(session_user, "Adjust PartDB Stock"):
        return

    draw_header(session_user, "PartDB Stock Receiving & Inventory Adjustment", active_tab_key="partdb")
    target_id_str = smart_input("Enter PartDB Part ID # to adjust stock:", allow_empty=False, numpad=True, session_user=session_user)
    if target_id_str in ["__BACK__", "__QUIT__"] or not target_id_str.isdigit():
        return

    part_id = int(target_id_str)
    try:
        conn = sqlite3.connect(PARTDB_DB_PATH)
        c = conn.cursor()
        p = c.execute("SELECT id, name FROM parts WHERE id = ?", (part_id,)).fetchone()
        if not p:
            print(f"{C_RED}❌ Part ID #{part_id} not found in PartDB.{CLR_RESET}")
            conn.close()
            press_enter_to_continue()
            return

        lot = c.execute("SELECT id, amount FROM part_lots WHERE id_part = ? LIMIT 1", (part_id,)).fetchone()
        current_amount = lot[1] if lot else 0.0
        lot_id = lot[0] if lot else None

        print(f"\n{C_WHITE}Component:{CLR_RESET} {C_YELLOW}{p[1]} (#{p[0]}){CLR_RESET}")
        print(f"{C_WHITE}Current Stock:{CLR_RESET} {C_GREEN}{current_amount} pcs{CLR_RESET}\n")

        adjust_str = smart_input("Quantity to Add (+ or -) e.g. 5 or -2:", allow_empty=False, numpad=True, session_user=session_user)
        if adjust_str in ["__BACK__", "__QUIT__"]: return

        try:
            qty_delta = float(adjust_str)
        except ValueError:
            print(f"{C_RED}❌ Quantity must be a number.{CLR_RESET}")
            conn.close()
            press_enter_to_continue()
            return

        new_amount = max(0.0, current_amount + qty_delta)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if lot_id:
            c.execute("UPDATE part_lots SET amount = ?, last_modified = ? WHERE id = ?", (new_amount, now_str, lot_id))
        else:
            c.execute("""
                INSERT INTO part_lots (id_store_location, id_part, description, comment, instock_unknown, 
                                       amount, needs_refill, last_modified, datetime_added)
                VALUES (1, ?, 'Stock adjustment', '', 0, ?, 0, ?, ?)
            """, (part_id, new_amount, now_str, now_str))

        conn.commit()
        conn.close()

        # Register Undo Handler
        def undo_adjust():
            c2 = sqlite3.connect(PARTDB_DB_PATH)
            if lot_id:
                c2.execute("UPDATE part_lots SET amount = ? WHERE id = ?", (current_amount, lot_id))
            c2.commit()
            c2.close()

        TOUCH_ENGINE.undo_stack.push(f"Adjusted Stock for Part #{part_id} ({qty_delta:+} pcs)", undo_adjust)

        print(f"\n{C_GREEN}✅ Stock Updated for Part #{part_id} ({p[1]}){CLR_RESET}")
        print(f"   Previous Qty: {current_amount} pcs")
        print(f"   New Qty:      {C_BOLD}{C_GREEN}{new_amount} pcs{CLR_RESET}")

        log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "ADJUST_PARTDB_STOCK", "SUCCESS", f"PART_ID:#{part_id}, DELTA:{qty_delta}, NEW_QTY:{new_amount}")
        TOUCH_ENGINE.show_toast(f"Stock adjusted ({qty_delta:+} pcs)! Tap [Undo] to revert.")

    except Exception as e:
        print(f"{C_RED}❌ Error updating PartDB stock: {e}{CLR_RESET}")

    press_enter_to_continue()

def module_partdb_hub(session_user: dict):
    """Master menu hub for PartDB operations."""
    while True:
        draw_header(session_user, "PartDB Terminal Component & Inventory Hub", active_tab_key="partdb")
        print(f"{C_YELLOW}Select PartDB Management Option:{CLR_RESET}")
        print(f" {C_CYAN}[1]{CLR_RESET} {ICO_SEARCH}  Search & Browse PartDB Inventory")
        print(f" {C_CYAN}[2]{CLR_RESET} 🔩  Create New Part in PartDB")
        print(f" {C_CYAN}[3]{CLR_RESET} 📦  Receive / Adjust PartDB Stock Quantities")
        print(f" {C_CYAN}[0]{CLR_RESET} ↩️   Return to Main Navigation Hub\n")

        TOUCH_ENGINE.register_hitbox(13, 13, 1, 50, "OPTION_1")
        TOUCH_ENGINE.register_hitbox(14, 14, 1, 50, "OPTION_2")
        TOUCH_ENGINE.register_hitbox(15, 15, 1, 50, "OPTION_3")
        TOUCH_ENGINE.register_hitbox(16, 16, 1, 50, "ACTION_BACK")

        choice = smart_input("Select Option [1-3, Q]:", allow_empty=True, session_user=session_user)
        if choice in ["0", "b", "q", "__BACK__", "ACTION_BACK"]: break
        elif choice.startswith("__TAB_"): return choice
        elif choice in ["1", "OPTION_1"]:
            res = module_partdb_browse(session_user)
            if res and str(res).startswith("__TAB_"): return res
        elif choice in ["2", "OPTION_2"]:
            res = module_partdb_create(session_user)
            if res and str(res).startswith("__TAB_"): return res
        elif choice in ["3", "OPTION_3"]:
            res = module_partdb_stock_adjust(session_user)
            if res and str(res).startswith("__TAB_"): return res

# =============================================================================
# ⚡ TASK MODULE: INTERACTIVE SCRIPT RUNNER HUB
# =============================================================================

def discover_scripts():
    """Scans /root/scripts/ for executable script files and extracts docstrings."""
    if not os.path.exists(SCRIPTS_DIR):
        return []

    files = glob.glob(os.path.join(SCRIPTS_DIR, "*"))
    scripts = []
    for f in sorted(files):
        if os.path.isdir(f): continue
        filename = os.path.basename(f)
        if filename.startswith(".") or filename in ["tui_audit.log", "modernwms_tui.py"]: continue

        doc = "No description available."
        try:
            with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
                lines = [fp.readline() for _ in range(15)]
                doc_lines = []
                in_doc = False
                for line in lines:
                    if '"""' in line or "'''" in line:
                        if in_doc: break
                        in_doc = True
                        continue
                    if in_doc:
                        doc_lines.append(line.strip())
                if doc_lines:
                    doc = " ".join(doc_lines[:2])
        except Exception:
            pass

        scripts.append({
            "name": filename,
            "path": f,
            "desc": doc[:65] + ".." if len(doc) > 65 else doc
        })
    return scripts

def module_script_runner(session_user: dict):
    """Interactive script discovery and runner hub."""
    while True:
        draw_header(session_user, "Interactive Script Hub (/root/scripts/)", active_tab_key="scripts")
        scripts = discover_scripts()

        if not scripts:
            print(f"{C_YELLOW}No scripts found in {SCRIPTS_DIR}{CLR_RESET}")
            press_enter_to_continue()
            return

        print(f"{C_WHITE}Discovered Executable Scripts in /root/scripts/:{CLR_RESET}\n")
        y_start = 13
        for idx, s in enumerate(scripts, start=1):
            y_curr = y_start + idx - 1
            TOUCH_ENGINE.register_hitbox(y_curr, y_curr, 1, 75, f"OPTION_SCRIPT_{idx}")
            print(f" {C_CYAN}[{idx}]{CLR_RESET} {ICO_SCRIPT} {C_BOLD}{C_WHITE}{s['name']:<28}{CLR_RESET} {C_DIM}{s['desc']}{CLR_RESET}")

        print(f"\n {C_CYAN}[A]{CLR_RESET} 📜  View Security Audit Log (/root/tui_audit.log)")
        print(f" {C_CYAN}[0]{CLR_RESET} ↩️   Return to Main Navigation Hub\n")

        TOUCH_ENGINE.register_hitbox(y_start + len(scripts) + 1, y_start + len(scripts) + 1, 1, 50, "OPTION_AUDIT")
        TOUCH_ENGINE.register_hitbox(y_start + len(scripts) + 2, y_start + len(scripts) + 2, 1, 50, "ACTION_BACK")

        choice = smart_input(f"Select Script # [1-{len(scripts)}, A, Q]:", allow_empty=True, session_user=session_user)
        if choice in ["0", "q", "__BACK__", "ACTION_BACK"]: break
        elif choice.startswith("__TAB_"): return choice
        elif choice in ["a", "A", "OPTION_AUDIT"]:
            if os.path.exists(AUDIT_LOG_FILE):
                with open(AUDIT_LOG_FILE, 'r') as f:
                    log_data = f.readlines()
                inspect_record_modal({f"Log Line #{i+1}": line.strip() for i, line in enumerate(log_data[-15:])}, title="Security Audit Log")
            else:
                print(f"{C_YELLOW}No audit log file found.{CLR_RESET}")
                press_enter_to_continue()
        else:
            s_idx = None
            if choice.startswith("OPTION_SCRIPT_"):
                s_idx = int(choice.replace("OPTION_SCRIPT_", "")) - 1
            elif choice.isdigit() and 1 <= int(choice) <= len(scripts):
                s_idx = int(choice) - 1

            if s_idx is not None and 0 <= s_idx < len(scripts):
                target_script = scripts[s_idx]
                print(f"\n{C_BOLD}{C_CYAN}Running {target_script['name']}...{CLR_RESET}\n")
                args_input = smart_input("Enter CLI Arguments (or ENTER for default):", allow_empty=True, session_user=session_user)
                if args_input == "__BACK__": continue

                cmd = [sys.executable, target_script['path']]
                if args_input:
                    cmd.extend(args_input.split())

                log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "EXECUTE_SCRIPT", "STARTED", f"SCRIPT:{target_script['name']}")
                subprocess.run(cmd)
                log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "EXECUTE_SCRIPT", "COMPLETED", f"SCRIPT:{target_script['name']}")
                press_enter_to_continue()

# =============================================================================
# 📦 TASK MODULE: INBOUND ASN & WMS OPERATIONS
# =============================================================================

def module_receive_stock(session_user: dict):
    """Generates formal ModernWMS Inbound ASN stock receipt with Undo support."""
    if not check_write_permission(session_user, "Receive Stock (ASN)"):
        return

    draw_header(session_user, "Notice on Arrival (Inbound ASN Putaway)", active_tab_key="asn")
    identifier = smart_input("Commodity Code, SPU Name, or ID:", allow_empty=False, session_user=session_user)
    if identifier in ["__BACK__", "__QUIT__"] or not identifier: return

    qty_str = smart_input("Quantity to Receive (pcs):", allow_empty=False, numpad=True, session_user=session_user)
    if qty_str in ["__BACK__", "__QUIT__"]: return

    try:
        qty = int(qty_str)
    except ValueError:
        print(f"{C_RED}❌ Invalid quantity.{CLR_RESET}")
        press_enter_to_continue()
        return

    rcv_script = os.path.join(SCRIPTS_DIR, "receive_stock.py")
    if os.path.exists(rcv_script):
        proc = subprocess.run([sys.executable, rcv_script, identifier, str(qty)], capture_output=True, text=True)
        print(proc.stdout)
        if proc.stderr: print(proc.stderr)
        log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "RECEIVE_STOCK_ASN", "SUCCESS", f"ITEM:{identifier}, QTY:{qty}")
        TOUCH_ENGINE.show_toast(f"Received {qty} pcs for '{identifier}'!")
    else:
        print(f"{C_RED}❌ Script /root/scripts/receive_stock.py not found.{CLR_RESET}")

    press_enter_to_continue()

def module_stock_lookup(session_user: dict):
    """ModernWMS Inventory balance lookup."""
    draw_header(session_user, "Inventory & Commodity Balance Directory", active_tab_key="stock_lookup")
    search = smart_input("Enter Commodity Name, Code, or SPU ID [Enter for all]:", allow_empty=True, session_user=session_user)
    if search in ["__BACK__", "__QUIT__"] or search.startswith("__TAB_"): return

    s_json = json.dumps(f"%{search}%")
    script = f'''
import sqlite3, json
conn = sqlite3.connect("{DB_PATH}")
c = conn.cursor()
search_pattern = {s_json}

rows = c.execute("""
    SELECT s.id, sp.spu_code, sp.spu_name, s.qty, s.is_freeze, s.last_update_time
    FROM stock s
    JOIN spu sp ON s.sku_id = sp.id
    WHERE sp.spu_name LIKE ? OR sp.spu_code LIKE ? OR sp.id LIKE ?
    LIMIT 40
""", (search_pattern, search_pattern, search_pattern)).fetchall()
conn.close()

print(json.dumps(rows))
'''
    res = run_db_script(script)
    try:
        rows = json.loads(res)
        print(f"\n{C_BOLD}{C_WHITE}{'Stock ID':<10} {'SPU Code':<15} {'SPU Name':<30} {'Qty Balance':<15} {'Status':<10}{CLR_RESET}")
        print(f"{C_CYAN}──────────────────────────────────────────────────────────────────────────────{CLR_RESET}")
        if not rows:
            print(f"{C_YELLOW}No stock records found.{CLR_RESET}")
        else:
            for r in rows:
                s_id, code, name, qty, freeze, utime = r
                st_str = f"{C_RED}FROZEN{CLR_RESET}" if freeze else f"{C_GREEN}NORMAL{CLR_RESET}"
                print(f"{C_CYAN}#{s_id:<9}{CLR_RESET} {C_GRAY}{code:<15}{CLR_RESET} {C_WHITE}{name:<30}{CLR_RESET} {C_BOLD}{C_GREEN}{qty:<15.0f}{CLR_RESET} {st_str}")
    except Exception as e:
        print(f"{C_RED}❌ Error reading WMS stock: {e}{CLR_RESET}")

    press_enter_to_continue()

def module_master_data(session_user: dict):
    """Master Data directory (SPUs, Suppliers, Customers)."""
    draw_header(session_user, "Master Data Directory (SPUs, Suppliers, Customers)", active_tab_key="master_data")
    print(f"{C_YELLOW}Master Data Directory Options:{CLR_RESET}")
    print(f" {C_CYAN}[1]{CLR_RESET} View Commodity SPUs")
    print(f" {C_CYAN}[2]{CLR_RESET} View Registered Suppliers")
    print(f" {C_CYAN}[3]{CLR_RESET} View Registered Customers")
    print(f" {C_CYAN}[0]{CLR_RESET} Return\n")

    TOUCH_ENGINE.register_hitbox(12, 12, 1, 40, "OPTION_1")
    TOUCH_ENGINE.register_hitbox(13, 13, 1, 40, "OPTION_2")
    TOUCH_ENGINE.register_hitbox(14, 14, 1, 40, "OPTION_3")
    TOUCH_ENGINE.register_hitbox(15, 15, 1, 40, "ACTION_BACK")

    c = smart_input("Choice [1-3, Q]:", allow_empty=True, session_user=session_user)
    if c in ["1", "OPTION_1"]:
        res = run_db_script('import sqlite3, json; conn=sqlite3.connect("/app/wms.db"); c=conn.cursor(); rows=c.execute("SELECT id, spu_code, spu_name FROM spu LIMIT 30").fetchall(); conn.close(); print(json.dumps(rows))')
        inspect_record_modal({f"SPU #{r[0]}": f"{r[1]} - {r[2]}" for r in json.loads(res)}, title="Master SPUs")
    elif c in ["2", "OPTION_2"]:
        res = run_db_script('import sqlite3, json; conn=sqlite3.connect("/app/wms.db"); c=conn.cursor(); rows=c.execute("SELECT id, supplier_name FROM supplier LIMIT 30").fetchall(); conn.close(); print(json.dumps(rows))')
        inspect_record_modal({f"Supplier #{r[0]}": r[1] for r in json.loads(res)}, title="Suppliers")
    elif c in ["3", "OPTION_3"]:
        res = run_db_script('import sqlite3, json; conn=sqlite3.connect("/app/wms.db"); c=conn.cursor(); rows=c.execute("SELECT id, customer_name FROM customer LIMIT 30").fetchall(); conn.close(); print(json.dumps(rows))')
        inspect_record_modal({f"Customer #{r[0]}": r[1] for r in json.loads(res)}, title="Customers")

def module_user_management(session_user: dict):
    """ModernWMS & PartDB Full Enterprise User & Access Management Hub."""
    if not check_write_permission(session_user, "User Security Management"): return

    while True:
        draw_header(session_user, "User & Security Administration", active_tab_key="user_mgmt")
        print(f"{C_CYAN}User & Access Control Administration Hub:{CLR_RESET}\n")
        print(f" {C_YELLOW}[1]{CLR_RESET} 📋 List All Registered Users (ModernWMS & PartDB)")
        print(f" {C_YELLOW}[2]{CLR_RESET} ➕ Create New User (Auto-Generated Secure Temp Password)")
        print(f" {C_YELLOW}[3]{CLR_RESET} 🔑 Reset User Password (Random Temp PW or Custom)")
        print(f" {C_YELLOW}[4]{CLR_RESET} ✏️  Modify User Role & Email")
        print(f" {C_YELLOW}[5]{CLR_RESET} 🛡️  Toggle User Active / Disabled Status")
        print(f" {C_YELLOW}[6]{CLR_RESET} 🗑️  Delete User Account")
        print(f" {C_YELLOW}[0]{CLR_RESET} 🔙 Return to Main Menu\n")

        TOUCH_ENGINE.register_hitbox(12, 12, 1, 60, "OPTION_1")
        TOUCH_ENGINE.register_hitbox(13, 13, 1, 60, "OPTION_2")
        TOUCH_ENGINE.register_hitbox(14, 14, 1, 60, "OPTION_3")
        TOUCH_ENGINE.register_hitbox(15, 15, 1, 60, "OPTION_4")
        TOUCH_ENGINE.register_hitbox(16, 16, 1, 60, "OPTION_5")
        TOUCH_ENGINE.register_hitbox(17, 17, 1, 60, "OPTION_6")
        TOUCH_ENGINE.register_hitbox(18, 18, 1, 60, "ACTION_BACK")

        choice = smart_input("Select Option [1-6, Q]:", allow_empty=True, session_user=session_user)
        if choice in ["0", "q", "Q", "ACTION_BACK", "__BACK__", "__QUIT__"]:
            break

        # [1] LIST ALL USERS
        if choice in ["1", "OPTION_1"]:
            draw_header(session_user, "Registered Users Directory", active_tab_key="user_mgmt")
            users = user_manager.list_all_users()
            print(f"{CLR_BOLD}{'SYSTEM':<11} | {'ID':<4} | {'USERNAME':<15} | {'ROLE / GROUP':<18} | {'STATUS':<9} | {'TEMP PW?':<10} | {'EMAIL'}{CLR_RESET}")
            print(f"{C_CYAN}{'─' * 96}{CLR_RESET}")
            for u in users:
                status_color = C_GREEN if u['is_valid'] else C_RED
                status_str = f"{status_color}{'ACTIVE' if u['is_valid'] else 'DISABLED'}{CLR_RESET}"
                temp_color = C_YELLOW if u['must_change_pw'] else C_GRAY
                temp_str = f"{temp_color}{'YES (FORCE)' if u['must_change_pw'] else 'NO'}{CLR_RESET}"
                print(f"{C_WHITE}{u['system']:<11}{CLR_RESET} | {u['id']:<4} | {C_YELLOW}{u['username']:<15}{CLR_RESET} | {u['role']:<18} | {status_str:<18} | {temp_str:<19} | {u['email']}")
            print(f"\n{C_DIM}Total Registered Users across Ecology: {len(users)}{CLR_RESET}\n")
            press_enter_to_continue()

        # [2] CREATE NEW USER
        elif choice in ["2", "OPTION_2"]:
            draw_header(session_user, "Create New User Wizard", active_tab_key="user_mgmt")
            print(f"{C_YELLOW}Select Target Authentication Engine:{CLR_RESET}")
            print(f" {C_CYAN}[1]{CLR_RESET} Unified (Both ModernWMS & PartDB) - {C_GREEN}Recommended{CLR_RESET}")
            print(f" {C_CYAN}[2]{CLR_RESET} ModernWMS Warehouse Only")
            print(f" {C_CYAN}[3]{CLR_RESET} PartDB Components Only")
            print(f" {C_CYAN}[0]{CLR_RESET} Cancel\n")

            sys_c = smart_input("Target System [1-3, Q]:", allow_empty=True, session_user=session_user)
            if sys_c in ["0", "q", "Q", "__BACK__", "__QUIT__"]:
                continue

            u_name = smart_input("🔑 New Username / User ID (required):", allow_empty=False, session_user=session_user)
            if u_name in ["__BACK__", "__QUIT__"]: continue

            u_email = smart_input("✉️  Email Address (optional):", allow_empty=True, session_user=session_user)
            if u_email in ["__BACK__", "__QUIT__"]: continue

            print(f"\n{C_YELLOW}Select User Role / Access Tier:{CLR_RESET}")
            print(f" {C_CYAN}[1]{CLR_RESET} Operator / Picker (Standard Warehouse Ops)")
            print(f" {C_CYAN}[2]{CLR_RESET} Administrator (Full System Management)")
            print(f" {C_CYAN}[3]{CLR_RESET} View-Only (Restricted Read Access)")
            r_c = smart_input("Select Role [1-3, default 1]:", allow_empty=True, session_user=session_user)
            
            if r_c == "2":
                role_str = "Admin"
            elif r_c == "3":
                role_str = "ViewOnly"
            else:
                role_str = "Picker"

            print(f"\n{C_YELLOW}Password Setup Mode:{CLR_RESET}")
            print(f" {C_CYAN}[1]{CLR_RESET} Auto-Generate Secure Random Temp Password ({C_GREEN}Forced Reset on Login{CLR_RESET})")
            print(f" {C_CYAN}[2]{CLR_RESET} Enter Custom Password")
            p_mode = smart_input("Password Mode [1/2, default 1]:", allow_empty=True, session_user=session_user)

            custom_pwd = None
            is_temp = True
            if p_mode == "2":
                custom_pwd = smart_input("Enter Custom Password:", allow_empty=False, is_password=True, session_user=session_user)
                if custom_pwd in ["__BACK__", "__QUIT__"]: continue
                is_temp = False

            if sys_c == "2":
                ok, msg, gen_pwd = user_manager.create_modernwms_user(u_name, role=role_str, email=u_email, custom_password=custom_pwd, temp_password=is_temp)
                target_label = "ModernWMS"
            elif sys_c == "3":
                ok, msg, gen_pwd = user_manager.create_partdb_user(u_name, role=role_str, email=u_email, custom_password=custom_pwd, temp_password=is_temp)
                target_label = "PartDB"
            else:
                ok, msg, gen_pwd = user_manager.create_unified_user(u_name, role=role_str, email=u_email, custom_password=custom_pwd, temp_password=is_temp)
                target_label = "ModernWMS & PartDB"

            if ok:
                clear_screen()
                print(f"{C_GREEN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  {ICO_CHECK} {CLR_BOLD}{C_WHITE}USER ACCOUNT CREATED SUCCESSFULLY!{CLR_RESET}                                   {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  System Target:    {C_CYAN}{target_label:<56}{CLR_RESET} {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  Username:         {C_YELLOW}{u_name:<56}{CLR_RESET} {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  Role / Tier:      {C_WHITE}{role_str:<56}{CLR_RESET} {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  Email:            {C_DIM}{u_email or 'N/A':<56}{CLR_RESET} {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  {ICO_LOCK} {CLR_BOLD}Assigned Password:{CLR_RESET} {BG_BLUE}{C_WHITE}{CLR_BOLD} {gen_pwd} {CLR_RESET}                                      {C_GREEN}│{CLR_RESET}")
                if is_temp:
                    print(f"{C_GREEN}│{CLR_RESET}  {C_YELLOW}⚠️  SECURITY NOTICE: User is forced to change password on first login.{CLR_RESET}      {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")
            else:
                print(f"\n{C_RED}❌ {msg}{CLR_RESET}\n")
            press_enter_to_continue()

        # [3] RESET PASSWORD
        elif choice in ["3", "OPTION_3"]:
            draw_header(session_user, "Reset User Password", active_tab_key="user_mgmt")
            u_in = smart_input("🔑 Username or ID to reset:", allow_empty=False, session_user=session_user)
            if u_in in ["__BACK__", "__QUIT__"]: continue

            print(f"\n{C_YELLOW}Password Reset Options:{CLR_RESET}")
            print(f" {C_CYAN}[1]{CLR_RESET} Generate Random Temporary Password ({C_GREEN}Forces New Password on Login{CLR_RESET})")
            print(f" {C_CYAN}[2]{CLR_RESET} Enter Specific New Password")
            mode = smart_input("Select Reset Mode [1/2, default 1]:", allow_empty=True, session_user=session_user)

            custom_pwd = None
            is_temp = True
            if mode == "2":
                custom_pwd = smart_input("Enter New Password:", allow_empty=False, is_password=True, session_user=session_user)
                if custom_pwd in ["__BACK__", "__QUIT__"]: continue
                is_temp = False

            ok, msg, gen_pwd = user_manager.reset_unified_password(u_in, new_password=custom_pwd, is_temp=is_temp)
            if ok:
                clear_screen()
                print(f"{C_GREEN}╭──────────────────────────────────────────────────────────────────────────────╮{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  {ICO_CHECK} {CLR_BOLD}{C_WHITE}PASSWORD RESET SUCCESSFUL!{CLR_RESET}                                         {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}├──────────────────────────────────────────────────────────────────────────────┤{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  Target User:      {C_YELLOW}{u_in:<56}{CLR_RESET} {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}│{CLR_RESET}  {ICO_LOCK} {CLR_BOLD}New Password:{CLR_RESET}     {BG_BLUE}{C_WHITE}{CLR_BOLD} {gen_pwd} {CLR_RESET}                                      {C_GREEN}│{CLR_RESET}")
                if is_temp:
                    print(f"{C_GREEN}│{CLR_RESET}  {C_YELLOW}⚠️  SECURITY NOTICE: User must set a permanent password on next login.{CLR_RESET}     {C_GREEN}│{CLR_RESET}")
                print(f"{C_GREEN}╰──────────────────────────────────────────────────────────────────────────────╯{CLR_RESET}\n")
            else:
                print(f"\n{C_RED}❌ {msg}{CLR_RESET}\n")
            press_enter_to_continue()

        # [4] MODIFY USER
        elif choice in ["4", "OPTION_4"]:
            draw_header(session_user, "Modify User Role & Email", active_tab_key="user_mgmt")
            u_in = smart_input("👤 Username or ID to modify:", allow_empty=False, session_user=session_user)
            if u_in in ["__BACK__", "__QUIT__"]: continue

            print(f"\n{C_YELLOW}Select New Role / Tier (Leave empty to keep current):{CLR_RESET}")
            print(f" {C_CYAN}[1]{CLR_RESET} Picker (Operator)")
            print(f" {C_CYAN}[2]{CLR_RESET} Admin")
            print(f" {C_CYAN}[3]{CLR_RESET} ViewOnly")
            print(f" {C_CYAN}[Enter]{CLR_RESET} Keep Current Role")
            r_c = smart_input("Role Choice [1-3]:", allow_empty=True, session_user=session_user)
            
            new_role = None
            if r_c == "1": new_role = "Picker"
            elif r_c == "2": new_role = "Admin"
            elif r_c == "3": new_role = "ViewOnly"

            new_email = smart_input("New Email (or Enter to keep current):", allow_empty=True, session_user=session_user)
            if new_email in ["__BACK__", "__QUIT__"]: continue
            if not new_email: new_email = None

            w_ok, w_msg = user_manager.modify_modernwms_user(u_in, role=new_role, email=new_email)
            p_ok, p_msg = user_manager.modify_partdb_user(u_in, role=new_role, email=new_email)

            if w_ok or p_ok:
                print(f"\n{C_GREEN}{ICO_CHECK} User '{u_in}' updated successfully across systems.{CLR_RESET}")
            else:
                print(f"\n{C_RED}❌ Failed to update user '{u_in}': {w_msg} | {p_msg}{CLR_RESET}")
            press_enter_to_continue()

        # [5] TOGGLE USER STATUS (ENABLE / DISABLE)
        elif choice in ["5", "OPTION_5"]:
            draw_header(session_user, "Toggle User Active / Disabled Status", active_tab_key="user_mgmt")
            u_in = smart_input("👤 Username or ID:", allow_empty=False, session_user=session_user)
            if u_in in ["__BACK__", "__QUIT__"]: continue

            print(f"\n{C_YELLOW}Select Desired Status:{CLR_RESET}")
            print(f" {C_GREEN}[1] ENABLE / ACTIVATE Account{CLR_RESET}")
            print(f" {C_RED}[2] DISABLE Account{CLR_RESET}")
            s_c = smart_input("Choice [1/2]:", allow_empty=True, session_user=session_user)
            if s_c in ["1", "2"]:
                is_val = 1 if s_c == "1" else 0
                w_ok, _ = user_manager.modify_modernwms_user(u_in, is_valid=is_val)
                p_ok, _ = user_manager.modify_partdb_user(u_in, is_valid=is_val)
                status_label = "ENABLED" if is_val == 1 else "DISABLED"
                if w_ok or p_ok:
                    print(f"\n{C_GREEN}{ICO_CHECK} Account '{u_in}' is now {status_label}.{CLR_RESET}")
                else:
                    print(f"\n{C_RED}❌ User '{u_in}' not found.{CLR_RESET}")
            press_enter_to_continue()

        # [6] DELETE USER
        elif choice in ["6", "OPTION_6"]:
            draw_header(session_user, "Delete User Account", active_tab_key="user_mgmt")
            u_in = smart_input("⚠️ Username or ID to DELETE:", allow_empty=False, session_user=session_user)
            if u_in in ["__BACK__", "__QUIT__"]: continue

            confirm = smart_input(f"{C_RED}Are you SURE you want to permanently delete user '{u_in}'? (type 'yes' to confirm):{CLR_RESET}", allow_empty=True, session_user=session_user)
            if confirm.strip().lower() == "yes":
                w_ok, w_msg = user_manager.delete_user("modernwms", u_in)
                p_ok, p_msg = user_manager.delete_user("partdb", u_in)
                if w_ok or p_ok:
                    print(f"\n{C_GREEN}{ICO_CHECK} User '{u_in}' deleted successfully.{CLR_RESET}")
                else:
                    print(f"\n{C_RED}❌ {w_msg} | {p_msg}{CLR_RESET}")
            else:
                print(f"\n{C_YELLOW}Deletion cancelled.{CLR_RESET}")
            press_enter_to_continue()

def module_delivery_management(session_user: dict):
    """Outbound Delivery Dispatches."""
    draw_header(session_user, "Outbound Delivery & Dispatch Orders", active_tab_key="delivery")
    res = run_db_script('import sqlite3, json; conn=sqlite3.connect("/app/wms.db"); c=conn.cursor(); rows=c.execute("SELECT id, dispatch_no, dispatch_status FROM dispatchlist LIMIT 20").fetchall(); conn.close(); print(json.dumps(rows))')
    try:
        rows = json.loads(res)
        inspect_record_modal({f"Dispatch #{r[0]}": f"No:{r[1]} Status:{r[2]}" for r in rows}, title="Outbound Dispatches")
    except Exception:
        press_enter_to_continue()

def module_docker_dashboard(session_user: dict):
    """Multi-Container Ecology Suite & System Control."""
    draw_header(session_user, "Multi-Container Ecology Suite & Control", active_tab_key="docker")
    print(f"{C_WHITE}Running Containers in Ecology:{CLR_RESET}\n")
    subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'])
    press_enter_to_continue()

# =============================================================================
# 🏠 MAIN MASTER NAVIGATION HUB LOOP
# =============================================================================

def main_tui_loop():
    TOUCH_ENGINE.enable_mouse()
    session_user = login_prompt()
    current_tab = "dashboard"

    while True:
        draw_header(session_user, "Master Navigation Hub", active_tab_key=current_tab)

        menu_items = [
            ("dashboard", "1", ICO_CHART, "Executive Dual KPI Dashboard & Multi-System Analytics"),
            ("partdb", "2", ICO_PART, "PartDB Terminal Component Creator & Inventory Hub"),
            ("scripts", "3", ICO_SCRIPT, "Interactive Script Runner Hub (Discover & Run /root/scripts)")
        ]

        if is_module_allowed(session_user, "asn"):
            menu_items.append(("asn", "4", ICO_BOX, "Notice on Arrival (Inbound ASN Putaway)"))
        if is_module_allowed(session_user, "warehouse_ops"):
            menu_items.append(("warehouse_ops", "5", ICO_WH, "Warehouse Operations (Move, Freeze, Adjust, Stocktaking)"))
        if is_module_allowed(session_user, "stock_lookup"):
            menu_items.append(("stock_lookup", "6", "🔍", "Stock Inventory & Commodity Balance Lookup"))
        if is_module_allowed(session_user, "master_data"):
            menu_items.append(("master_data", "7", "📋", "Master Data Directory (SPUs, Suppliers, Customers)"))
        if is_module_allowed(session_user, "user_mgmt"):
            menu_items.append(("user_mgmt", "8", ICO_USER, "User Security & Password Management"))
        if is_module_allowed(session_user, "delivery"):
            menu_items.append(("delivery", "9", ICO_TRUCK, "Outbound Delivery & Dispatch Orders"))
        if is_module_allowed(session_user, "docker"):
            menu_items.append(("docker", "d", ICO_DOCKER, "Multi-Container Ecology Suite & System Control"))

        print(f"{C_YELLOW}Main Navigation Hub Touch Cards:{CLR_RESET}")
        y_start = 12
        for idx, (key, num, icon, label) in enumerate(menu_items):
            highlight = f"{C_BOLD}{C_CYAN}▶{CLR_RESET} " if key == current_tab else "  "
            y_curr = y_start + idx
            TOUCH_ENGINE.register_hitbox(y_curr, y_curr, 1, 75, f"SELECT_MENU_{key}")
            print(f"{highlight}{C_CYAN}[{num}]{CLR_RESET} {icon}  {label}")

        print(f"\n  {C_CYAN}[L]{CLR_RESET} {ICO_LOCK}  Lock Session / Switch User")
        print(f"  {C_CYAN}[Q]{CLR_RESET} 🚪  Exit TUI Control Suite\n")

        TOUCH_ENGINE.register_hitbox(y_start + len(menu_items) + 1, y_start + len(menu_items) + 1, 1, 40, "ACTION_LOCK")
        TOUCH_ENGINE.register_hitbox(y_start + len(menu_items) + 2, y_start + len(menu_items) + 2, 1, 40, "ACTION_EXIT")

        draw_footer()
        choice_str = smart_input("Select Option or Tap Screen [1-9, D, L, Q]:", allow_empty=True, session_user=session_user).strip().lower()

        if choice_str in ["q", "exit", "__QUIT__", "ACTION_EXIT"]:
            print(f"\n{C_CYAN}Session logged out. Returning to login...{CLR_RESET}\n")
            log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "LOGOUT", "SUCCESS")
            time.sleep(0.5)
            session_user = login_prompt()
            continue


        if choice_str in ["l", "lock", "ACTION_LOCK"]:
            print(f"\n{C_YELLOW}Session locked.{CLR_RESET}")
            log_audit_event(session_user.get("user_name"), session_user.get("user_role"), "SESSION_LOCK", "SUCCESS")
            time.sleep(1)
            session_user = login_prompt()
            continue

        selected_item = None
        if choice_str.startswith("__TAB_"):
            selected_item = choice_str.replace("__TAB_", "").replace("__", "")
        elif choice_str.startswith("SELECT_MENU_"):
            selected_item = choice_str.replace("SELECT_MENU_", "")
        else:
            for key, num, icon, label in menu_items:
                if choice_str == num.lower() or choice_str == key:
                    selected_item = key
                    break

        if not selected_item:
            try:
                c_idx = int(choice_str)
                if 1 <= c_idx <= len(menu_items):
                    selected_item = menu_items[c_idx - 1][0]
            except ValueError:
                continue

        if selected_item:
            current_tab = selected_item
            if selected_item == "dashboard":
                module_overview_dashboard(session_user)
            elif selected_item == "partdb":
                module_partdb_hub(session_user)
            elif selected_item == "scripts":
                module_script_runner(session_user)
            elif selected_item == "asn":
                module_receive_stock(session_user)
            elif selected_item == "warehouse_ops":
                module_partdb_stock_adjust(session_user)
            elif selected_item == "stock_lookup":
                module_stock_lookup(session_user)
            elif selected_item == "master_data":
                module_master_data(session_user)
            elif selected_item == "user_mgmt":
                module_user_management(session_user)
            elif selected_item == "delivery":
                module_delivery_management(session_user)
            elif selected_item == "docker":
                module_docker_dashboard(session_user)

if __name__ == "__main__":
    import signal
    def _sig_handler(sig, frame):
        TOUCH_ENGINE.disable_mouse()
        sys.stdout.write("\033[?1000l\033[?1006l")
        sys.stdout.flush()
        print(f"\n\n{C_CYAN}TUI session terminated by signal.{CLR_RESET}\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        main_tui_loop()
    except KeyboardInterrupt:
        print(f"\n\n{C_CYAN}TUI session closed by user.{CLR_RESET}\n")
    finally:
        TOUCH_ENGINE.disable_mouse()
        sys.stdout.write("\033[?1000l\033[?1006l")
        sys.stdout.flush()

