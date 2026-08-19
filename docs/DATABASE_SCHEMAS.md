# Database Schemas: PartDB & ModernWMS

This document defines the underlying database schemas, field mappings, and foreign key relationships for both systems.

---

## 1. PartDB SQLite Database Schema (`app.db`)

PartDB stores component metadata, engineering specifications, stock lots, categories, and manufacturers.

### `parts` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique PartDB Part ID |
| `name` | VARCHAR(255) | NOT NULL | Part Name / Specification Code |
| `description` | CLOB | NOT NULL | Part Description |
| `comment` | CLOB | NOT NULL | Internal Notes / Comments |
| `ipn` | VARCHAR(100) | UNIQUE | Internal Part Number |
| `gtin` | VARCHAR(255) | NULL | Barcode / GTIN |
| `manufacturer_product_number` | VARCHAR(255) | NOT NULL | Mfg Part Number (Commodity Code) |
| `id_category` | INTEGER | NOT NULL, FK -> categories(id) | Category Reference |
| `mass` | DOUBLE | NULL | Part weight/mass in grams |
| `minamount` | DOUBLE | NOT NULL | Minimum safety stock threshold |
| `needs_review` | BOOLEAN | NOT NULL | Verification flag |
| `datetime_added` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `last_modified` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Update timestamp |

### `part_lots` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Lot / Stock Entry ID |
| `id_part` | INTEGER | NOT NULL, FK -> parts(id) | Reference to Part |
| `id_store_location` | INTEGER | NULL, FK -> storelocations(id) | Physical Storage Location |
| `amount` | DOUBLE | NOT NULL | Lot stock quantity |
| `needs_refill` | BOOLEAN | NOT NULL | Refill flag |
| `vendor_barcode` | CLOB | NULL | Lot-specific vendor barcode |
| `datetime_added` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

### `categories` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Category ID |
| `parent_id` | INTEGER | NULL, FK -> categories(id) | Parent category for hierarchy |
| `name` | VARCHAR(255) | NOT NULL | Category name |

---

## 2. ModernWMS SQLite Database Schema (`wms.db`)

ModernWMS manages warehouse operations, inventory tracking, ASNs (Advance Shipping Notices), picking, dispatches, and role-based permissions.

### `spu` (Standard Product Unit) Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | SPU ID (Mapped to PartDB `parts.id`) |
| `spu_code` | TEXT | NOT NULL | Commodity Code (Mfg PN / IPN) |
| `spu_name` | TEXT | NOT NULL | Specification Code (Part Name) |
| `category_id` | INTEGER | NOT NULL | Mapped to PartDB Category ID |
| `spu_description`| TEXT | NOT NULL | Full part description & notes |
| `bar_code` | TEXT | NOT NULL | GTIN or Barcode string |
| `supplier_id` | INTEGER | NOT NULL | Supplier ID (Default `1` - KCLEGO) |
| `supplier_name`| TEXT | NOT NULL | Supplier Name (`KCLEGO`) |
| `creator` | TEXT | NOT NULL | Creator User Num (`7354`) |
| `is_valid` | INTEGER | NOT NULL (1 = Active) | Soft delete flag |
| `tenant_id` | INTEGER | NOT NULL (1) | Tenant isolation ID |

### `sku` (Stock Keeping Unit) Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | SKU ID (1:1 with SPU) |
| `spu_id` | INTEGER | NOT NULL, FK -> spu(id) | SPU Reference |
| `sku_code` | TEXT | NOT NULL | SKU Identifier Code |
| `sku_name` | TEXT | NOT NULL | SKU Display Name |
| `weight` | TEXT | NOT NULL | Unit weight |
| `unit` | TEXT | NOT NULL | Unit of measure (e.g. `pcs`) |

### `stock` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Stock Record ID |
| `sku_id` | INTEGER | NOT NULL | Reference to SKU / SPU |
| `goods_location_id` | INTEGER | NOT NULL | Location ID (`1` = KCLEGO) |
| `qty` | INTEGER | NOT NULL | Current on-hand quantity |
| `goods_owner_id` | INTEGER | NOT NULL | Owner ID (`1` = Default Owner) |
| `is_freeze` | INTEGER | NOT NULL (0 = Unfrozen) | Freeze flag |
| `last_update_time` | TEXT | NOT NULL | Timestamp of last stock change |

### `asn` (Notice on Arrival / Stock Receiving) Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ASN Record ID |
| `asn_no` | TEXT | NOT NULL | Unique Ticket No (`ASN20260819...`) |
| `asn_status` | INTEGER | NOT NULL (4 = Sorted/Complete)| Status of receipt |
| `spu_id` | INTEGER | NOT NULL | Part SPU ID |
| `sku_id` | INTEGER | NOT NULL | Part SKU ID |
| `asn_qty` | INTEGER | NOT NULL | Expected arrival quantity |
| `actual_qty` | INTEGER | NOT NULL | Confirmed received quantity |
| `sorted_qty` | INTEGER | NOT NULL | Quantity placed into stock |
| `supplier_name`| TEXT | NOT NULL | `KCLEGO` |
| `creator` | TEXT | NOT NULL | User who processed arrival (`7354`) |

### `user` & `user_security` Tables
* **`user`**: `id`, `user_num`, `user_name`, `auth_string` (MD5 Hash), `user_role`, `email`, `is_valid`, `tenant_id`.
* **`user_security`**: `user_id` (PK), `must_change_pw` (1 = Force change on next login), `temp_pw_created_at` (ISO timestamp).

---

## 3. Entity Mapping (PartDB ➔ ModernWMS)

| PartDB Entity / Field | ModernWMS Entity / Field | Sync Transformation Rule |
| :--- | :--- | :--- |
| `parts.id` | `spu.id` & `sku.id` | Preserved 1:1 for seamless cross-linking |
| `parts.manufacturer_product_number` | `spu.spu_code` & `sku.sku_code` | Used as ModernWMS Commodity Code; fallback to IPN/Name |
| `parts.name` | `spu.spu_name` & `sku.sku_name` | Used as ModernWMS Specification Code |
| `categories.id` | `category.id` | Direct 1:1 ID sync |
| `SUM(part_lots.amount)` | `stock.qty` | Consolidated to location `KCLEGO` (id=1) |
| `parts.gtin` | `spu.bar_code` | Barcode scanning identifier |
