#!/usr/bin/env python3
"""
ModernWMS Stock Receiving Helper (Notice on Arrival / ASN Automated Receipt)
Adds stock to any part in ModernWMS by generating a formal ASN receipt and updating stock totals.

Usage:
  python3 /root/receive_stock.py <part_name_or_code_or_id> <quantity>
  receive-stock <part_name_or_code_or_id> <quantity>

Example:
  receive-stock 2780 3
"""

import sys
import json
import datetime
import os

CONTAINER = os.environ.get("MODERNWMS_CONTAINER", "modernwms")
DB_PATH = os.environ.get("MODERNWMS_DB_PATH", "/app/wms.db")

def receive_stock(identifier: str, qty_to_add: int):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    asn_no = "ASN" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    script = f'''
import sqlite3, json

conn = sqlite3.connect("{DB_PATH}")
c = conn.cursor()

identifier = {json.dumps(identifier)}
qty_to_add = {int(qty_to_add)}
now = "{now_str}"
asn_no = "{asn_no}"

# Find part in spu
part = c.execute("""
    SELECT id, spu_code, spu_name, spu_description 
    FROM spu 
    WHERE spu_name = ? OR spu_code = ? OR id = ? OR spu_description LIKE ?
    LIMIT 1
""", (identifier, identifier, identifier, f"%{{identifier}}%")).fetchone()

if not part:
    print(json.dumps({{"error": f"Part '{{identifier}}' not found in ModernWMS."}}))
    conn.close()
    exit(0)

p_id, spu_code, spu_name, spu_desc = part

# Ensure stock record exists
stock = c.execute("SELECT id, qty FROM stock WHERE sku_id = ? AND goods_location_id = 1", (p_id,)).fetchone()
if not stock:
    c.execute("""
        INSERT INTO stock (sku_id, goods_location_id, qty, goods_owner_id, is_freeze, last_update_time, tenant_id)
        VALUES (?, 1, 0, 1, 0, ?, 1)
    """, (p_id, now))
    prev_qty = 0
else:
    prev_qty = stock[1]

new_qty = prev_qty + qty_to_add

# 1. Insert ASN record (Notice on Arrival)
c.execute("""
    INSERT INTO asn (asn_no, asn_status, spu_id, sku_id, asn_qty, actual_qty, sorted_qty, shortage_qty, more_qty, damage_qty, weight, volume, supplier_id, supplier_name, goods_owner_id, goods_owner_name, creator, create_time, last_update_time, is_valid, tenant_id)
    VALUES (?, 4, ?, ?, ?, ?, ?, 0, 0, 0, '0.0', '0.0', 1, 'KCLEGO', 1, 'Default Owner', '7354', ?, ?, 1, 1)
""", (asn_no, p_id, p_id, qty_to_add, qty_to_add, qty_to_add, now, now))
asn_id = c.lastrowid

# 2. Insert ASN Sort record
c.execute("""
    INSERT INTO asnsort (asn_id, sorted_qty, creator, create_time, last_update_time, is_valid, tenant_id)
    VALUES (?, ?, '7354', ?, ?, 1, 1)
""", (asn_id, qty_to_add, now, now))

# 3. Update stock total
c.execute("UPDATE stock SET qty = ?, last_update_time = ? WHERE sku_id = ? AND goods_location_id = 1", (new_qty, now, p_id))

conn.commit()
conn.close()

print(json.dumps({{
    "status": "success",
    "asn_no": asn_no,
    "part_id": p_id,
    "spu_code": spu_code,
    "spu_name": spu_name,
    "added_qty": qty_to_add,
    "previous_qty": prev_qty,
    "new_qty": new_qty
}}))
'''

    proc = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'python3', '-'], input=script, capture_output=True, text=True)
    if proc.returncode != 0:
        print("❌ Error running receiving script:", proc.stderr)
        return

    res = json.loads(proc.stdout.strip())
    if "error" in res:
        print(f"❌ Error: {res['error']}")
        return

    print("\n📦 ModernWMS Stock Receipt Complete (Notice on Arrival / ASN)")
    print("=" * 60)
    print(f"Receipt Ticket (ASN):  {res['asn_no']}")
    print(f"Part Name:             {res['spu_name']} (ID #{res['part_id']})")
    print(f"Commodity Code:        {res['spu_code']}")
    print(f"Supplier / Location:   KCLEGO (Main Warehouse)")
    print(f"Quantity Added:        +{res['added_qty']} pcs")
    print(f"Previous Stock:        {res['previous_qty']} pcs")
    print(f"New Stock Total:       {res['new_qty']} pcs")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] in ["-h", "--help"]:
        print("ModernWMS Stock Receiving Helper Tool")
        print("Usage: receive-stock <part_name_or_code_or_id> <quantity_to_add>")
        print("Example: receive-stock 2780 3")
        sys.exit(0)

    part_id = sys.argv[1]
    try:
        qty = int(sys.argv[2])
    except ValueError:
        print("Error: Quantity must be a valid integer.")
        sys.exit(1)

    receive_stock(part_id, qty)
