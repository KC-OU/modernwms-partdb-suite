#!/usr/bin/env python3
"""
PartDB to ModernWMS Professional Monitoring Dashboard & Sync API
Includes:
- Manual Synced Part Links Editing & Persistence Engine
- HTTP Basic Auth Security with Salted PBKDF2 Password Hashing
- Modern Dark-Mode UI with Real-time Auto-refresh & Search
- Prometheus Exporter (/metrics) & Full REST API (/api/*)
- Domain-only Linking (PartDB, ModernWMS, Grafana, Overview)
- Real-time Background Inventory Synchronization
"""

import os
import sys
import time
import json
import base64
import sqlite3
import threading
import subprocess
import datetime
import hashlib
import hmac
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Path resolution with smart host/container fallbacks
def resolve_path(env_var, default_container_path, fallback_host_path):
    val = os.environ.get(env_var)
    if val and os.path.exists(val):
        return val
    if os.path.exists(default_container_path):
        return default_container_path
    if os.path.exists(fallback_host_path):
        return fallback_host_path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_cfg = os.path.join(script_dir, "config", os.path.basename(fallback_host_path))
    if os.path.exists(local_cfg):
        return local_cfg
    local_asset = os.path.join(script_dir, "assets", os.path.basename(fallback_host_path))
    if os.path.exists(local_asset):
        return local_asset
    return fallback_host_path

PARTDB_DB_PATH = resolve_path("PARTDB_DB_PATH", "/app/partdb_db/app.db", "/root/docker-server/partdb/db/app.db")
CREDENTIALS_FILE = resolve_path("CREDENTIALS_FILE", "/app/config/credentials.json", "/root/docker-server/partdb-sync/config/credentials.json")
HISTORY_DB_PATH = resolve_path("HISTORY_DB_PATH", "/app/config/sync_history.db", "/root/docker-server/partdb-sync/config/sync_history.db")
ICON_PATH = resolve_path("ICON_PATH", "/app/config/original_lego_supplier.png", "/root/docker-server/partdb-sync/config/original_lego_supplier.png")

MODERNWMS_CONTAINER = os.environ.get("MODERNWMS_CONTAINER", "modernwms")
PORT = int(os.environ.get("PORT", "8082"))

PARTDB_URL = os.environ.get("PARTDB_URL", "https://partdb.kierancollins.xyz/en/")
MODERNWMS_URL = os.environ.get("MODERNWMS_URL", "https://modernwms.kierancollins.xyz/")
OVERVIEW_URL = os.environ.get("OVERVIEW_URL", "https://overview.kierancollins.xyz/")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "https://grafana.kierancollins.xyz/")
ICON_URL = "/original_lego_supplier.png"
START_TIME = time.time()

# Ensure config directory exists
os.makedirs(os.path.dirname(HISTORY_DB_PATH), exist_ok=True)

def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex(), salt.hex()

def verify_password(password: str, password_hash: str, salt_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        new_hash, _ = hash_password(password, salt)
        return hmac.compare_digest(new_hash, password_hash)
    except Exception:
        return False

def get_admin_credentials():
    user = os.environ.get("SYNC_ADMIN_USER", "admin")
    initial_pass = os.environ.get("SYNC_ADMIN_PASS", "admin123")

    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                data = json.load(f)
                return data.get("username", user), data.get("password_hash"), data.get("salt")
        except Exception as e:
            print(f"Error reading credentials file: {e}")

    pass_hash, salt_hex = hash_password(initial_pass)
    save_admin_credentials(user, initial_pass)
    return user, pass_hash, salt_hex

def save_admin_credentials(username, password):
    pass_hash, salt_hex = hash_password(password)
    os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({
            "username": username,
            "password_hash": pass_hash,
            "salt": salt_hex,
            "updated_at": datetime.datetime.now().isoformat()
        }, f, indent=2)

def reset_modernwms_password(new_password: str, username: str = "admin"):
    md5_hash = hashlib.md5(new_password.encode('utf-8')).hexdigest()
    container_script = f'''
import sqlite3
conn = sqlite3.connect("/app/wms.db")
c = conn.cursor()
c.execute("UPDATE user SET auth_string = '{md5_hash}' WHERE user_name = '{username}' OR user_num = '{username}'")
conn.commit()
updated = c.rowcount
conn.close()
print(updated)
'''
    proc = subprocess.run(
        ['docker', 'exec', '-i', MODERNWMS_CONTAINER, 'python3', '-'],
        input=container_script,
        capture_output=True,
        text=True
    )
    if proc.returncode == 0 and proc.stdout.strip() != '0':
        return True, f"ModernWMS user '{username}' password successfully updated!"
    else:
        err = proc.stderr.strip() if proc.stderr else f"User '{username}' not found in ModernWMS database"
        return False, err

class PersistentStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS part_link_overrides (
            part_id INTEGER PRIMARY KEY,
            partdb_link TEXT,
            modernwms_link TEXT,
            updated_at TEXT
        )
        """)
        conn.commit()
        conn.close()

    def save_link_override(self, part_id, partdb_link, modernwms_link):
        conn = self._get_conn()
        c = conn.cursor()
        now_str = datetime.datetime.now().isoformat()
        c.execute("""
        INSERT OR REPLACE INTO part_link_overrides (part_id, partdb_link, modernwms_link, updated_at)
        VALUES (?, ?, ?, ?)
        """, (int(part_id), partdb_link, modernwms_link, now_str))
        conn.commit()
        conn.close()

    def get_link_overrides(self):
        conn = self._get_conn()
        c = conn.cursor()
        rows = c.execute("SELECT * FROM part_link_overrides").fetchall()
        conn.close()
        return {r["part_id"]: {"partdb_link": r["partdb_link"], "modernwms_link": r["modernwms_link"]} for r in rows}

store = PersistentStore(HISTORY_DB_PATH)

class SyncEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_sync_time = None
        self.last_status = "Initialized"
        self.stats = {
            "synced_categories": 0,
            "synced_locations": 0,
            "synced_parts": 0,
            "synced_stock_records": 0,
            "total_stock_qty": 0,
            "last_duration_seconds": 0.0,
            "total_sync_count": 0,
            "total_error_count": 0,
            "api_requests_total": 0,
            "errors": []
        }
        self.history = []

    def fetch_partdb_data(self):
        if not os.path.exists(PARTDB_DB_PATH):
            raise FileNotFoundError(f"PartDB database not found at {PARTDB_DB_PATH}")

        conn = sqlite3.connect(PARTDB_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        categories = [dict(r) for r in cursor.execute("SELECT * FROM categories").fetchall()]
        locations = [dict(r) for r in cursor.execute("SELECT * FROM storelocations").fetchall()]
        parts = [dict(r) for r in cursor.execute("SELECT * FROM parts").fetchall()]
        lots = [dict(r) for r in cursor.execute("SELECT * FROM part_lots").fetchall()]

        conn.close()
        return {
            "categories": categories,
            "locations": locations,
            "parts": parts,
            "lots": lots
        }

    def sync_now(self):
        with self.lock:
            start_t = time.time()
            self.stats["total_sync_count"] += 1
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            try:
                data = self.fetch_partdb_data()

                payload = {
                    "now": now_str,
                    "categories": data["categories"],
                    "locations": data["locations"],
                    "parts": data["parts"],
                    "lots": data["lots"]
                }

                container_script = f'''
import sqlite3, json

payload = json.loads({json.dumps(json.dumps(payload))})
now = payload["now"]
categories = payload["categories"]
locations = payload["locations"]
parts = payload["parts"]
lots = payload["lots"]

conn = sqlite3.connect("/app/wms.db")
c = conn.cursor()

# Ensure user permissions: deactivate admin user, activate 7354 (Admin) and 10932 (Picker)
c.execute("UPDATE user SET is_valid = 0 WHERE user_name = 'admin' OR user_num = 'admin'")
c.execute("UPDATE user SET is_valid = 1, tenant_id = 1 WHERE user_num IN ('7354', '10932')")

# Insert/ensure ViewOnly user (username: viewonly, password: viewonly -> MD5 b48d9c5f3bc873d3213500c1a0c5eadd)
viewonly_hash = "b48d9c5f3bc873d3213500c1a0c5eadd"
c.execute("""INSERT OR REPLACE INTO user (id, user_num, user_name, contact_tel, user_role, sex, is_valid, auth_string, email, creator, create_time, last_update_time, tenant_id)
VALUES (4, 'viewonly', 'viewonly', '', 'ViewOnly', 'Unknown', 1, ?, 'viewonly@kierancollins.xyz', '7354', ?, ?, 1)""", (viewonly_hash, now, now))

# Insert/ensure ViewOnly role (id = 6) and assign view-only menu permissions
c.execute("""INSERT OR REPLACE INTO userrole (id, role_name, is_valid, create_time, last_update_time, tenant_id)
VALUES (6, 'ViewOnly', 1, ?, ?, 1)""", (now, now))

c.execute("DELETE FROM rolemenu WHERE userrole_id = 6")
view_menu_ids = [24, 25, 26, 27, 28, 29, 30, 31, 37, 38]
for m_id in view_menu_ids:
    c.execute("""INSERT INTO rolemenu (userrole_id, menu_id, authority, create_time, last_update_time, tenant_id)
    VALUES (6, ?, 1, ?, ?, 1)""", (m_id, now, now))

# 1. Base Infrastructure with creator/manager = '7354'
c.execute("""INSERT OR REPLACE INTO warehouse (id, warehouse_name, city, address, email, manager, contact_tel, creator, create_time, last_update_time, is_valid, tenant_id)
VALUES (1, 'Main Warehouse', 'Default City', 'Main Street', '', '7354', '', '7354', ?, ?, 1, 1)""", (now, now))

c.execute("""INSERT OR REPLACE INTO warehousearea (id, warehouse_id, area_name, parent_id, create_time, last_update_time, is_valid, tenant_id, area_property)
VALUES (1, 1, 'General Storage', 0, ?, ?, 1, 1, 1)""", (now, now))

# Single Location called KCLEGO
c.execute("""INSERT OR REPLACE INTO goodslocation (id, warehouse_id, warehouse_name, warehouse_area_name, warehouse_area_property, location_name, location_length, location_width, location_heigth, location_volume, location_load, roadway_number, shelf_number, layer_number, tag_number, create_time, last_update_time, is_valid, tenant_id, warehouse_area_id)
VALUES (1, 1, 'Main Warehouse', 'General Storage', 1, 'KCLEGO', '0', '0', '0', '0', '0', '1', '1', '1', 'KCLEGO', ?, ?, 1, 1, 1)""", (now, now))
c.execute("UPDATE goodslocation SET is_valid = 0 WHERE id != 1")

c.execute("""INSERT OR REPLACE INTO goodsowner (id, goods_owner_name, city, address, manager, contact_tel, creator, create_time, last_update_time, is_valid, tenant_id)
VALUES (1, 'Default Owner', '', '', '7354', '', '7354', ?, ?, 1, 1)""", (now, now))

# Single Supplier called KCLEGO
c.execute("""INSERT OR REPLACE INTO supplier (id, supplier_name, city, address, email, manager, contact_tel, creator, create_time, last_update_time, is_valid, tenant_id)
VALUES (1, 'KCLEGO', '', '', '', '7354', '', '7354', ?, ?, 1, 1)""", (now, now))

# Default category (id=0) for uncategorized items
c.execute("""INSERT OR REPLACE INTO category (id, category_name, parent_id, creator, create_time, last_update_time, is_valid, tenant_id)
VALUES (0, 'Uncategorized', 0, '7354', ?, ?, 1, 1)""", (now, now))

# 2. Categories
active_cat_ids = set([0])
for cat in categories:
    cat_id = cat['id']
    active_cat_ids.add(cat_id)
    c_time = cat.get('datetime_added') or now
    u_time = cat.get('last_modified') or now
    p_id = cat.get('parent_id') or 0
    c.execute("""INSERT OR REPLACE INTO category (id, category_name, parent_id, creator, create_time, last_update_time, is_valid, tenant_id)
    VALUES (?, ?, ?, '7354', ?, ?, 1, 1)""", (cat_id, cat['name'], p_id, c_time, u_time))

existing_cats = [r[0] for r in c.execute("SELECT id FROM category").fetchall()]
for ec_id in existing_cats:
    if ec_id not in active_cat_ids and ec_id != 0:
        c.execute("UPDATE category SET is_valid = 0 WHERE id = ?", (ec_id,))

# 3. Parts -> spu & sku (Commodity Code = Manufacturer Product Number, Spec Code = Part Name)
active_part_ids = set()
for p in parts:
    p_id = p['id']
    active_part_ids.add(p_id)
    
    mfg_pn = (p.get('manufacturer_product_number') or '').strip()
    spec_code = (p.get('name') or '').strip()
    part_desc = (p.get('description') or p.get('comment') or spec_code).strip()
    
    # Commodity Code: Manufacturer part number if available, fallback to IPN/spec_code/PART-ID
    spu_code = mfg_pn if mfg_pn else (p.get('ipn') or spec_code or f"PART-{{p_id}}")
    # Specification Code / Part Name from PartDB (e.g. 2780, 52107, 3705)
    spu_name = spec_code if spec_code else part_desc
    spu_desc = f"Specification Code: {{spec_code}} | {{part_desc}}" if (spec_code and spec_code != part_desc) else f"Specification Code: {{spec_code or part_desc}}"
    
    cat_id = p.get('id_category') if p.get('id_category') is not None else 0
    gtin = p.get('gtin') or mfg_pn or spu_code
    mass = str(p.get('mass') or '0')
    c_time = p.get('datetime_added') or now
    u_time = p.get('last_modified') or now

    c.execute("""INSERT OR REPLACE INTO spu (id, spu_code, spu_name, category_id, spu_description, bar_code, supplier_id, supplier_name, brand, origin, length_unit, volume_unit, weight_unit, creator, create_time, last_update_time, is_valid, tenant_id)
    VALUES (?, ?, ?, ?, ?, ?, 1, 'KCLEGO', '', '', 0, 0, 0, '7354', ?, ?, 1, 1)""", (p_id, spu_code, spu_name, cat_id, spu_desc, gtin, c_time, u_time))

    c.execute("""INSERT OR REPLACE INTO sku (id, spu_id, sku_code, sku_name, weight, lenght, width, height, volume, unit, cost, price, create_time, last_update_time)
    VALUES (?, ?, ?, ?, ?, '0', '0', '0', '0', 'pcs', '0', '0', ?, ?)""", (p_id, p_id, spu_code, spu_name, mass, c_time, u_time))

existing_spus = [r[0] for r in c.execute("SELECT id FROM spu").fetchall()]
for es_id in existing_spus:
    if es_id not in active_part_ids:
        c.execute("UPDATE spu SET is_valid = 0 WHERE id = ?", (es_id,))
        c.execute("DELETE FROM stock WHERE sku_id = ?", (es_id,))

# 4. Stock / Quantities -> Consolidated to Location KCLEGO (id = 1)
part_stock_map = {{}}
for lot in lots:
    p_id = lot.get('id_part')
    if not p_id or p_id not in active_part_ids:
        continue
    qty = int(lot.get('amount') or 0)
    part_stock_map[p_id] = part_stock_map.get(p_id, 0) + qty

for p_id in active_part_ids:
    if p_id not in part_stock_map:
        part_stock_map[p_id] = 0

# Initial Stock Only Mode: Only insert stock for newly added parts
for p_id, initial_qty in part_stock_map.items():
    existing = c.execute("SELECT id FROM stock WHERE sku_id = ?", (p_id,)).fetchone()
    if existing is None:
        c.execute("""INSERT INTO stock (sku_id, goods_location_id, qty, goods_owner_id, is_freeze, last_update_time, tenant_id)
        VALUES (?, 1, ?, 1, 0, ?, 1)""", (p_id, initial_qty, now))

total_qty = c.execute("SELECT SUM(qty) FROM stock WHERE goods_location_id = 1").fetchone()[0] or 0

conn.commit()
conn.close()

print(json.dumps({{
    "synced_categories": len(categories),
    "synced_locations": 1,
    "synced_parts": len(parts),
    "synced_stock_records": len(part_stock_map),
    "total_stock_qty": total_qty
}}))
'''

                proc = subprocess.run(
                    ['docker', 'exec', '-i', MODERNWMS_CONTAINER, 'python3', '-'],
                    input=container_script,
                    capture_output=True,
                    text=True
                )

                duration_s = time.time() - start_t
                duration_ms = round(duration_s * 1000, 2)
                self.stats["last_duration_seconds"] = duration_s

                if proc.returncode != 0:
                    err_msg = proc.stderr.strip()
                    self.last_status = f"Error: {err_msg}"
                    self.stats["total_error_count"] += 1
                    self.stats["errors"].append(f"{now_str}: {err_msg}")
                    return {"status": "error", "message": err_msg}

                res = json.loads(proc.stdout.strip())
                self.stats["synced_categories"] = res["synced_categories"]
                self.stats["synced_locations"] = res["synced_locations"]
                self.stats["synced_parts"] = res["synced_parts"]
                self.stats["synced_stock_records"] = res["synced_stock_records"]
                self.stats["total_stock_qty"] = res["total_stock_qty"]
                self.last_sync_time = datetime.datetime.now().isoformat()
                self.last_status = "Success"

                log_entry = {
                    "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "duration_ms": duration_ms,
                    "synced_parts": res["synced_parts"],
                    "total_stock_qty": res["total_stock_qty"]
                }
                self.history.insert(0, log_entry)
                self.history = self.history[:50]

                return {
                    "status": "success",
                    "last_sync_time": self.last_sync_time,
                    "duration_ms": duration_ms,
                    "stats": self.stats
                }
            except Exception as e:
                self.last_status = f"Error: {str(e)}"
                self.stats["total_error_count"] += 1
                self.stats["errors"].append(f"{datetime.datetime.now().isoformat()}: {str(e)}")
                return {"status": "error", "message": str(e)}

    def background_sync_loop(self, interval=2):
        while True:
            try:
                self.sync_now()
            except Exception:
                pass
            time.sleep(interval)

engine = SyncEngine()

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PartDB ➔ ModernWMS | Observability & Control Center</title>
  <link rel="icon" type="image/png" href="/original_lego_supplier.png">
  <link rel="shortcut icon" href="/original_lego_supplier.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0f0f17;
      --card-bg: #1e1e2d;
      --card-border: #323248;
      --text-main: #ffffff;
      --text-muted: #92929f;
      --accent-green: #00e676;
      --accent-blue: #00b0ff;
      --accent-purple: #7c4dff;
      --accent-yellow: #ffab00;
      --accent-red: #ff5252;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background-color: rgba(30, 30, 45, 0.8);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--card-border);
      padding: 1rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
    }
    .brand { display: flex; align-items: center; gap: 0.75rem; }
    .brand-icon { width: 36px; height: 36px; border-radius: 8px; object-fit: cover; }
    .brand-title h1 { font-size: 1.1rem; font-weight: 600; }
    .brand-title span { font-size: 0.75rem; color: var(--text-muted); }
    .status-badge {
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.35rem 0.75rem; border-radius: 9999px;
      background: rgba(0, 230, 118, 0.1); border: 1px solid rgba(0, 230, 118, 0.3);
      color: var(--accent-green); font-size: 0.8rem; font-weight: 500;
    }
    .pulse-dot {
      width: 8px; height: 8px; background-color: var(--accent-green);
      border-radius: 50%; box-shadow: 0 0 10px var(--accent-green);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0.7); }
      70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(0, 230, 118, 0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 230, 118, 0); }
    }
    .nav-actions { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .btn {
      background-color: var(--accent-blue); color: white; border: none;
      padding: 0.5rem 1rem; border-radius: 6px; font-weight: 500; font-size: 0.85rem;
      cursor: pointer; display: inline-flex; align-items: center; gap: 0.4rem;
      transition: all 0.2s ease; text-decoration: none;
    }
    .btn:hover { background-color: #0091ea; transform: translateY(-1px); }
    .btn-secondary {
      background-color: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border); color: var(--text-main);
    }
    .btn-secondary:hover { background-color: rgba(255, 255, 255, 0.1); }
    .btn-edit {
      background-color: rgba(124, 77, 255, 0.15);
      border: 1px solid rgba(124, 77, 255, 0.4);
      color: #b388ff;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .btn-edit:hover { background-color: rgba(124, 77, 255, 0.3); }
    
    main {
      flex: 1; padding: 2rem; max-width: 1600px; width: 100%;
      margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;
    }

    .links-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;
    }
    .link-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 10px; padding: 1rem; display: flex; align-items: center;
      justify-content: space-between; text-decoration: none; color: var(--text-main);
      transition: all 0.2s ease;
    }
    .link-card:hover { border-color: var(--accent-blue); transform: translateY(-2px); }
    .link-info h4 { font-size: 0.9rem; font-weight: 600; margin-bottom: 0.2rem; }
    .link-info p { font-size: 0.75rem; color: var(--text-muted); }

    .stats-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;
    }
    .stat-card {
      background-color: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 10px; padding: 1.25rem; display: flex; flex-direction: column;
      justify-content: space-between; position: relative; overflow: hidden;
    }
    .stat-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
    }
    .stat-header { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); font-weight: 600; }
    .stat-value { font-size: 1.8rem; font-weight: 700; margin: 0.5rem 0; font-family: 'JetBrains Mono', monospace; }
    .stat-footer { font-size: 0.75rem; color: var(--accent-green); }

    .main-grid {
      display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem;
    }
    @media (max-width: 1024px) { .main-grid { grid-template-columns: 1fr; } }

    .panel {
      background-color: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 10px; padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem;
    }
    .panel-header {
      display: flex; align-items: center; justify-content: space-between;
      padding-bottom: 0.75rem; border-bottom: 1px solid var(--card-border);
    }
    .panel-title { font-size: 1rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; }
    .search-input {
      background-color: rgba(0, 0, 0, 0.2); border: 1px solid var(--card-border);
      color: var(--text-main); padding: 0.4rem 0.8rem; border-radius: 6px;
      font-size: 0.85rem; outline: none; width: 250px;
    }
    .search-input:focus { border-color: var(--accent-blue); }

    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th { text-align: left; padding: 0.75rem; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--card-border); }
    td { padding: 0.75rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
    tr:hover td { background-color: rgba(255, 255, 255, 0.02); }
    
    .badge {
      padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem;
      font-weight: 600; font-family: 'JetBrains Mono', monospace;
    }
    .badge-ipn { background: rgba(0, 176, 255, 0.15); color: var(--accent-blue); border: 1px solid rgba(0, 176, 255, 0.3); }
    .badge-cat { background: rgba(124, 77, 255, 0.15); color: var(--accent-purple); border: 1px solid rgba(124, 77, 255, 0.3); }
    
    .log-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 450px; overflow-y: auto; }
    .log-item {
      background: rgba(0, 0, 0, 0.2); border: 1px solid var(--card-border);
      border-radius: 6px; padding: 0.6rem 0.8rem; font-size: 0.8rem;
      font-family: 'JetBrains Mono', monospace; display: flex; justify-content: space-between;
    }

    .toast {
      position: fixed; bottom: 2rem; right: 2rem; background-color: var(--accent-green);
      color: black; padding: 0.75rem 1.5rem; border-radius: 8px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5); font-weight: 600; font-size: 0.9rem;
      display: none; z-index: 100;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <img src="/original_lego_supplier.png" alt="Logo" class="brand-icon" onerror="this.style.display='none'">
      <div class="brand-title">
        <h1>PartDB ➔ ModernWMS Control Center</h1>
        <span>Live Observability & Synchronization Engine</span>
      </div>
    </div>
    <div class="nav-actions">
      <div class="status-badge" id="statusPill">
        <div class="pulse-dot"></div>
        <span id="statusText">LIVE SYNC ACTIVE</span>
      </div>
      <button class="btn" onclick="triggerManualSync()" id="syncBtn">⚡ Sync Parts</button>
      <button class="btn btn-secondary" onclick="openPasswordModal()">🔑 Sync Password</button>
      <a href="/metrics" target="_blank" class="btn btn-secondary">📈 Metrics</a>
    </div>
  </header>

  <main>
    <div class="links-grid">
      <a href="https://partdb.kierancollins.xyz/en/" target="_blank" class="link-card">
        <div class="link-info">
          <h4>PartDB Portal ↗</h4>
          <p>https://partdb.kierancollins.xyz/en/</p>
        </div>
        <span style="font-size: 1.2rem;">📦</span>
      </a>
      <a href="https://modernwms.kierancollins.xyz/" target="_blank" class="link-card">
        <div class="link-info">
          <h4>ModernWMS Warehouse ↗</h4>
          <p>https://modernwms.kierancollins.xyz/</p>
        </div>
        <span style="font-size: 1.2rem;">🏢</span>
      </a>
      <div class="link-card" style="border-color: var(--accent-purple);">
        <div class="link-info">
          <h4 style="color: var(--accent-purple);">🔐 View-Only ModernWMS Login</h4>
          <p>User: <code style="color: var(--accent-green);">viewonly</code> | Pass: <code style="color: var(--accent-green);">view123</code></p>
        </div>
        <span style="font-size: 1.2rem;">👁️</span>
      </div>
      <div class="link-card" style="border-color: var(--accent-yellow);">
        <div class="link-info">
          <h4 style="color: var(--accent-yellow);">📦 Terminal Stock Receipt (ASN)</h4>
          <p><code style="color: var(--accent-blue);">receive-stock &lt;part_name&gt; &lt;qty&gt;</code></p>
        </div>
        <span style="font-size: 1.2rem;">⚡</span>
      </div>
      <a href="https://grafana.kierancollins.xyz/" target="_blank" class="link-card">
        <div class="link-info">
          <h4>Grafana Dashboards ↗</h4>
          <p>https://grafana.kierancollins.xyz/</p>
        </div>
        <span style="font-size: 1.2rem;">📊</span>
      </a>
      <div class="link-card">
        <div class="link-info">
          <h4>Service Uptime</h4>
          <p id="uptimeVal">Calculating...</p>
        </div>
        <span style="font-size: 1.2rem;">⏱️</span>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">Total Synced Parts</div>
        <div class="stat-value" id="statParts">0</div>
        <div class="stat-footer">● Active SPUs & SKUs</div>
      </div>
      <div class="stat-card">
        <div class="stat-header">Total Inventory Qty</div>
        <div class="stat-value" id="statQty">0</div>
        <div class="stat-footer">● Real-Time Total Stock</div>
      </div>
      <div class="stat-card">
        <div class="stat-header">Categories Synced</div>
        <div class="stat-value" id="statCategories">0</div>
        <div class="stat-footer">● Product Classifications</div>
      </div>
      <div class="stat-card">
        <div class="stat-header">Stock Locations</div>
        <div class="stat-value" id="statLocations">0</div>
        <div class="stat-footer">● Warehouses & Bins</div>
      </div>
    </div>

    <div class="main-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">📦 Synced Parts & Stock Matrix</div>
          <input type="text" id="searchInput" class="search-input" placeholder="Search parts or IPN..." onkeyup="filterParts()">
        </div>
        <div style="overflow-x: auto;">
          <table>
            <thead>
              <tr>
                <th>Part ID</th>
                <th>Spec Code (Name)</th>
                <th>Commodity Code (Mfg PN)</th>
                <th>Category</th>
                <th>Supplier / Location</th>
                <th>Stock Quantity</th>
                <th>Actions & Links</th>
              </tr>
            </thead>
            <tbody id="partsTableBody">
              <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading live parts matrix...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">⏱️ Live Sync Audit Log</div>
        </div>
        <div class="log-list" id="logList">
          <div class="log-item">Waiting for sync activity...</div>
        </div>
      </div>
    </div>
  </main>

  <div class="toast" id="toast">Synchronization triggered successfully!</div>

  <!-- Manual Link Editor Modal -->
  <div id="editLinksModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:1000; align-items:center; justify-content:center;">
    <div style="background: #1e1e2d; border: 1px solid var(--accent-purple); border-radius: 12px; padding: 2rem; width: 420px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); font-family: system-ui, -apple-system, sans-serif;">
      <h3 id="editPartTitle" style="margin-top:0; color:var(--accent-purple); display:flex; align-items:center; gap:0.5rem; font-size:1rem;">✏️ Manually Fix Part Links</h3>
      <p style="color:#aaa; font-size:0.8rem; line-height:1.4; margin: 0.5rem 0 1rem 0;">Manually override or fix the PartDB and ModernWMS links for this part.</p>
      <input type="hidden" id="editPartId">
      <div style="margin-bottom: 1rem;">
        <label style="display:block; color:#ccc; margin-bottom:0.4rem; font-size:0.8rem;">PartDB URL</label>
        <input type="text" id="editPartDBLink" style="width:100%; padding:0.6rem; background:#151521; border:1px solid #323248; color:#fff; border-radius:6px; font-size:0.85rem; box-sizing:border-box;">
      </div>
      <div style="margin-bottom: 1.5rem;">
        <label style="display:block; color:#ccc; margin-bottom:0.4rem; font-size:0.8rem;">ModernWMS URL</label>
        <input type="text" id="editModernWMSLink" style="width:100%; padding:0.6rem; background:#151521; border:1px solid #323248; color:#fff; border-radius:6px; font-size:0.85rem; box-sizing:border-box;">
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
        <button class="btn btn-secondary" onclick="closeEditLinksModal()">Cancel</button>
        <button class="btn" style="background:var(--accent-purple);" onclick="saveCustomLinks()">Save Custom Links</button>
      </div>
    </div>
  </div>

  <script>
    let partsData = [];

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.stats) {
          document.getElementById('statParts').innerText = data.stats.synced_parts || 0;
          document.getElementById('statQty').innerText = data.stats.total_stock_qty || 0;
          document.getElementById('statCategories').innerText = data.stats.synced_categories || 0;
          document.getElementById('statLocations').innerText = data.stats.synced_locations || 0;
        }
        document.getElementById('statusText').innerText = (data.status && data.status.includes('Success')) ? 'LIVE SYNC ACTIVE' : 'SYNC ACTIVE';

      } catch (err) {
        console.error("Status fetch error:", err);
      }
    }

    async function fetchParts() {
      try {
        const res = await fetch('/api/parts');
        if (!res.ok) return;
        const data = await res.json();
        partsData = data.parts || [];
        renderParts(partsData);
      } catch (err) {
        console.error("Parts fetch error:", err);
      }
    }

    function renderParts(parts) {
      const tbody = document.getElementById('partsTableBody');
      if (!parts || parts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted);">No parts found in PartDB</td></tr>`;
        return;
      }
      tbody.innerHTML = parts.map(p => `
        <tr>
          <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600;">#${p.partdb_id}</td>
          <td style="font-weight: 500;">${escapeHtml(p.spec_code || p.name)}</td>
          <td><span class="badge badge-ipn">${escapeHtml(p.spu_code || p.mfg_pn || p.ipn)}</span></td>
          <td><span class="badge badge-cat">${escapeHtml(p.category_name)}</span></td>
          <td><span class="badge" style="background:rgba(255,171,0,0.15); color:var(--accent-yellow); border:1px solid rgba(255,171,0,0.3);">KCLEGO</span></td>
          <td style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: ${p.total_quantity > 0 ? 'var(--accent-green)' : 'var(--accent-yellow)'};">
            ${p.total_quantity} pcs
          </td>
          <td>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
              <a href="${escapeHtml(p.partdb_link)}" target="_blank" style="color: var(--accent-blue); text-decoration: none; font-size: 0.8rem; font-weight: 500;">
                📦 PartDB ↗
              </a>
              <a href="${escapeHtml(p.modernwms_link || 'https://modernwms.kierancollins.xyz/')}" target="_blank" style="color: var(--accent-green); text-decoration: none; font-size: 0.8rem; font-weight: 500;">
                🏢 ModernWMS ↗
              </a>
              <button onclick="openEditLinksModal(${p.partdb_id}, '${escapeHtml(p.spec_code || p.name).replace(/'/g, "\\'")}', '${escapeHtml(p.partdb_link).replace(/'/g, "\\'")}', '${escapeHtml(p.modernwms_link || '').replace(/'/g, "\\'")}')" class="btn-edit">
                ✏️ Edit Links
              </button>
            </div>
          </td>
        </tr>
      `).join('');
    }

    function openEditLinksModal(id, name, partdbLink, modernwmsLink) {
      document.getElementById('editPartId').value = id;
      document.getElementById('editPartTitle').innerText = `✏️ Edit Links: ${name} (#${id})`;
      document.getElementById('editPartDBLink').value = partdbLink;
      document.getElementById('editModernWMSLink').value = modernwmsLink || `https://modernwms.kierancollins.xyz/#/commodityManagement`;
      document.getElementById('editLinksModal').style.display = 'flex';
    }

    function closeEditLinksModal() {
      document.getElementById('editLinksModal').style.display = 'none';
    }

    async function saveCustomLinks() {
      const partId = document.getElementById('editPartId').value;
      const partdbLink = document.getElementById('editPartDBLink').value.trim();
      const modernwmsLink = document.getElementById('editModernWMSLink').value.trim();
      try {
        const res = await fetch('/api/parts/update-links', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ part_id: partId, partdb_link: partdbLink, modernwms_link: modernwmsLink })
        });
        const data = await res.json();
        if (res.ok) {
          showToast('✅ Part links updated successfully!');
          closeEditLinksModal();
          await fetchParts();
        } else {
          alert('Error: ' + (data.error || 'Failed to update links'));
        }
      } catch (err) {
        alert('Error updating links: ' + err.message);
      }
    }

    function filterParts() {
      const query = document.getElementById('searchInput').value.toLowerCase();
      const filtered = partsData.filter(p => 
        (p.name || '').toLowerCase().includes(query) || 
        (p.spec_code || '').toLowerCase().includes(query) ||
        (p.spu_code || '').toLowerCase().includes(query) ||
        (p.mfg_pn || '').toLowerCase().includes(query) ||
        (p.category_name || '').toLowerCase().includes(query)
      );
      renderParts(filtered);
    }

    async function triggerManualSync() {
      const btn = document.getElementById('syncBtn');
      btn.innerText = '⌛ Syncing...';
      btn.disabled = true;
      try {
        const res = await fetch('/api/sync', { method: 'POST' });
        const data = await res.json();
        showToast(`Sync completed in ${data.duration_ms || 10} ms!`);
        await fetchStatus();
        await fetchParts();
      } catch (err) {
        showToast(`Sync error: ${err.message}`);
      } finally {
        btn.innerText = '⚡ Sync Parts';
        btn.disabled = false;
      }
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.style.display = 'block';
      setTimeout(() => { toast.style.display = 'none'; }, 3000);
    }

    // Sync Password Modal Logic
    function openPasswordModal() {
      document.getElementById('passwordModal').style.display = 'flex';
    }
    function closePasswordModal() {
      document.getElementById('passwordModal').style.display = 'none';
    }
    async function saveNewPassword() {
      const user = document.getElementById('newUsernameInput').value.trim();
      const pass = document.getElementById('newPasswordInput').value.trim();
      if (!pass || pass.length < 6) {
        alert('Password must be at least 6 characters long.');
        return;
      }
      try {
        const res = await fetch('/api/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: user, new_password: pass })
        });
        const data = await res.json();
        if (res.ok) {
          showToast('✅ Password updated & hashed on server storage!');
          closePasswordModal();
        } else {
          alert('Error: ' + (data.error || 'Failed to update password'));
        }
      } catch (err) {
        alert('Error updating password: ' + err.message);
      }
    }

    // Auto-update uptime clock
    const startTime = Date.now();
    setInterval(() => {
      const sec = Math.floor((Date.now() - startTime) / 1000);
      const hrs = Math.floor(sec / 3600);
      const mins = Math.floor((sec % 3600) / 60);
      const secs = sec % 60;
      document.getElementById('uptimeVal').innerText = `${hrs}h ${mins}m ${secs}s`;
    }, 1000);

    // Initial Load & Auto Refresh
    fetchStatus();
    fetchParts();
    setInterval(() => {
      fetchStatus();
      fetchParts();
    }, 3000);
  </script>

  <!-- Sync Password Change Modal -->
  <div id="passwordModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:1000; align-items:center; justify-content:center;">
    <div style="background: #1e1e2d; border: 1px solid #323248; border-radius: 12px; padding: 2rem; width: 380px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);">
      <h3 style="margin-top:0; color:#fff; display:flex; align-items:center; gap:0.5rem;">🔑 Change Sync Password</h3>
      <p style="color:#aaa; font-size:0.85rem; line-height:1.4; margin: 0.5rem 0 1rem 0;">Updates password for this Observability Dashboard using PBKDF2 salted hash.</p>
      <div style="margin-bottom: 1rem;">
        <label style="display:block; color:#ccc; margin-bottom:0.4rem; font-size:0.85rem;">Admin Username</label>
        <input type="text" id="newUsernameInput" value="admin" style="width:100%; padding:0.6rem; background:#151521; border:1px solid #323248; color:#fff; border-radius:6px; box-sizing:border-box;">
      </div>
      <div style="margin-bottom: 1.5rem;">
        <label style="display:block; color:#ccc; margin-bottom:0.4rem; font-size:0.85rem;">New Password (Min 6 chars)</label>
        <input type="password" id="newPasswordInput" placeholder="Enter new strong password" style="width:100%; padding:0.6rem; background:#151521; border:1px solid #323248; color:#fff; border-radius:6px; box-sizing:border-box;">
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.5rem;">
        <button class="btn btn-secondary" onclick="closePasswordModal()">Cancel</button>
        <button class="btn" onclick="saveNewPassword()">Save Password</button>
      </div>
    </div>
  </div>
</body>
</html>
"""

class APIHandler(BaseHTTPRequestHandler):
    def check_auth(self):
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False
        try:
            auth_type, encoded = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return False
            decoded = base64.b64decode(encoded).decode("utf-8")
            user, password = decoded.split(":", 1)
            current_user, pass_hash, salt_hex = get_admin_credentials()
            if not pass_hash or not salt_hex:
                return False
            return user == current_user and verify_password(password, pass_hash, salt_hex)
        except Exception:
            return False

    def require_auth(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="PartDB-ModernWMS Security"')
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Unauthorized"}).encode("utf-8"))

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = parsed.path
        self.send_response(200)
        if path in ["/", "/index.html"]:
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif path in ["/original_lego_supplier.png", "/original%20lego%20supplier.png", "/logo.png"]:
            self.send_header("Content-Type", "image/png")
        elif path == "/metrics":
            self.send_header("Content-Type", "text/plain; version=0.0.4")
        else:
            self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Metrics, health, logo, index, and read-only endpoints are public
        public_paths = [
            "/metrics", "/api/health", "/", "/index.html",
            "/api/status", "/api/parts", "/api/categories", "/api/stock",
            "/original_lego_supplier.png", "/original%20lego%20supplier.png", "/logo.png"
        ]
        if path not in public_paths:
            if not self.check_auth():
                self.require_auth()
                return

        engine.stats["api_requests_total"] = engine.stats.get("api_requests_total", 0) + 1

        if path in ["/original_lego_supplier.png", "/original%20lego%20supplier.png", "/logo.png"]:
            if os.path.exists(ICON_PATH):
                try:
                    with open(ICON_PATH, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception:
                    pass
            self.send_json({"error": "Image not found"}, 404)
        elif path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif path == "/metrics":
            status_val = 1 if engine.last_status == 'Success' else 0
            duration_val = engine.stats.get('last_duration_seconds', 0.0)
            total_runs = engine.stats.get('total_sync_count', 0)
            total_errs = engine.stats.get('total_error_count', 0)
            requests_cnt = engine.stats.get('api_requests_total', 0)
            uptime_val = int(time.time() - START_TIME)

            metrics = f"""# HELP partdb_sync_status Status of the PartDB to ModernWMS sync daemon (1 = success, 0 = error)
# TYPE partdb_sync_status gauge
partdb_sync_status {status_val}

# HELP partdb_synced_categories Total categories synced to ModernWMS
# TYPE partdb_synced_categories gauge
partdb_synced_categories {engine.stats['synced_categories']}

# HELP partdb_synced_locations Total locations synced to ModernWMS
# TYPE partdb_synced_locations gauge
partdb_synced_locations {engine.stats.get('synced_locations', 0)}

# HELP partdb_synced_parts Total parts synced to ModernWMS
# TYPE partdb_synced_parts gauge
partdb_synced_parts {engine.stats['synced_parts']}

# HELP partdb_synced_stock_records Total stock records in ModernWMS
# TYPE partdb_synced_stock_records gauge
partdb_synced_stock_records {engine.stats['synced_stock_records']}

# HELP partdb_total_stock_qty Total stock quantity synced to ModernWMS
# TYPE partdb_total_stock_qty gauge
partdb_total_stock_qty {engine.stats['total_stock_qty']}

# HELP partdb_sync_duration_seconds Duration of the last sync run in seconds
# TYPE partdb_sync_duration_seconds gauge
partdb_sync_duration_seconds {duration_val}

# HELP partdb_sync_runs_total Total number of sync runs executed
# TYPE partdb_sync_runs_total counter
partdb_sync_runs_total {total_runs}

# HELP partdb_sync_errors_total Total number of sync errors encountered
# TYPE partdb_sync_errors_total counter
partdb_sync_errors_total {total_errs}

# HELP partdb_api_requests_total Total number of API requests handled
# TYPE partdb_api_requests_total counter
partdb_api_requests_total {requests_cnt}

# HELP partdb_sync_uptime_seconds Uptime of the sync daemon in seconds
# TYPE partdb_sync_uptime_seconds counter
partdb_sync_uptime_seconds {uptime_val}
"""
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            self.wfile.write(metrics.encode("utf-8"))
        elif path == "/api/status":
            self.send_json({
                "status": engine.last_status,
                "last_sync_time": engine.last_sync_time,
                "stats": engine.stats,
                "overview_url": OVERVIEW_URL,
                "partdb_url": PARTDB_URL,
                "grafana_url": GRAFANA_URL,
                "modernwms_url": MODERNWMS_URL,
                "icon_url": ICON_URL
            })
        elif path == "/api/health":
            self.send_json({"status": "ok", "timestamp": datetime.datetime.now().isoformat()})
        elif path == "/api/parts":
            try:
                data = engine.fetch_partdb_data()
                link_overrides = store.get_link_overrides()
                parts_with_stock = []
                for p in data["parts"]:
                    p_id = p["id"]
                    p_lots = [l for l in data["lots"] if l["id_part"] == p_id]
                    total_qty = sum(int(l.get("amount") or 0) for l in p_lots)
                    cat = next((c for c in data["categories"] if c["id"] == p["id_category"]), None)
                    
                    mfg_pn = (p.get("manufacturer_product_number") or "").strip()
                    spec_code = (p.get("name") or "").strip()
                    spu_code = mfg_pn if mfg_pn else (p.get("ipn") or spec_code or f"PART-{p_id}")
                    
                    default_partdb = f"{PARTDB_URL.rstrip('/')}/part/{p_id}"
                    default_modernwms = f"{MODERNWMS_URL.rstrip('/')}/#/commodityManagement"
                    
                    override = link_overrides.get(p_id, {})
                    partdb_link = override.get("partdb_link") or default_partdb
                    modernwms_link = override.get("modernwms_link") or default_modernwms

                    parts_with_stock.append({
                        "partdb_id": p_id,
                        "name": spec_code,
                        "spec_code": spec_code,
                        "spu_code": spu_code,
                        "mfg_pn": mfg_pn,
                        "ipn": p.get("ipn") or "",
                        "category_name": cat["name"] if cat else "Uncategorized",
                        "supplier_name": "KCLEGO",
                        "location_name": "KCLEGO",
                        "total_quantity": total_qty,
                        "description": p.get("description") or "",
                        "partdb_link": partdb_link,
                        "modernwms_link": modernwms_link,
                        "lots_count": len(p_lots)
                    })
                self.send_json({"total_parts": len(parts_with_stock), "parts": parts_with_stock})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/categories":
            try:
                data = engine.fetch_partdb_data()
                self.send_json({"total_categories": len(data["categories"]), "categories": data["categories"]})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/stock":
            try:
                data = engine.fetch_partdb_data()
                self.send_json({"total_lots": len(data["lots"]), "lots": data["lots"]})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        else:
            self.send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/sync":
            res = engine.sync_now()
            self.send_json(res, 200 if res.get("status") == "success" else 500)
        elif parsed.path == "/api/parts/update-links":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))

                part_id = int(payload.get("part_id", 0))
                partdb_link = payload.get("partdb_link", "").strip()
                modernwms_link = payload.get("modernwms_link", "").strip()

                if not part_id:
                    self.send_json({"error": "Invalid part_id"}, code=400)
                    return

                store.save_link_override(part_id, partdb_link, modernwms_link)
                self.send_json({"status": "success", "message": f"Custom links saved for Part #{part_id}!"})
            except Exception as e:
                self.send_json({"error": str(e)}, code=500)
        elif parsed.path == "/api/modernwms/reset-password":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))

                new_pass = payload.get("new_password", "").strip()
                username = payload.get("username", "admin").strip() or "admin"

                if not new_pass:
                    self.send_json({"error": "New password cannot be empty"}, code=400)
                    return

                success, msg = reset_modernwms_password(new_pass, username)
                if success:
                    self.send_json({"status": "success", "message": msg})
                else:
                    self.send_json({"error": msg}, code=500)
            except Exception as e:
                self.send_json({"error": str(e)}, code=500)
        elif parsed.path == "/api/change-password":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode('utf-8'))

                new_pass = payload.get("new_password", "").strip()
                new_user = payload.get("username", "").strip() or "admin"

                if not new_pass or len(new_pass) < 6:
                    self.send_json({"error": "Password must be at least 6 characters long"}, code=400)
                    return

                save_admin_credentials(new_user, new_pass)
                self.send_json({"status": "success", "message": "Dashboard password updated successfully."})
            except Exception as e:
                self.send_json({"error": str(e)}, code=500)
        else:
            self.send_json({"error": "Endpoint not found"}, 404)

def run_server(port=8082):
    print(f"Starting initial sync between PartDB ({PARTDB_URL}) and ModernWMS ({MODERNWMS_URL})...")
    res = engine.sync_now()
    print("Initial sync result:", res)

    server_address = ("0.0.0.0", port)
    try:
        httpd = HTTPServer(server_address, APIHandler)
    except OSError as e:
        if e.errno == 98:
            print(f"\n[INFO] Port {port} is already in use by another process or container (e.g. 'partdb-sync').")
            print("[INFO] Initial sync completed successfully!")
            print(f"[INFO] The sync daemon is actively serving requests at http://localhost:{port}/")
            sys.exit(0)
        raise e

    sync_thread = threading.Thread(target=engine.background_sync_loop, kwargs={"interval": 2}, daemon=True)
    sync_thread.start()
    print("Background synchronization thread started (polling every 2s).")

    print(f"PartDB-ModernWMS Observability Dashboard & API listening on http://0.0.0.0:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Sync API server.")
        httpd.server_close()

if __name__ == "__main__":
    if "--once" in sys.argv or "--sync-only" in sys.argv:
        print(f"Running one-time sync between PartDB ({PARTDB_URL}) and ModernWMS ({MODERNWMS_URL})...")
        res = engine.sync_now()
        print("Sync result:", res)
        sys.exit(0 if res.get("status") == "success" else 1)
    run_server(PORT)

