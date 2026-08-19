# Google AI Studio Context Packet: ModernWMS & PartDB Unified Platform

> **Target Audience**: Google AI Studio (`aistudio.google.com`), Gemini 1.5 Pro / 2.0 Pro / Flash, Claude, or Codex.
> **Purpose**: Load this document into AI Studio as system instructions or background context to generate a modern unified web app, mobile app, or backend service.

---

## 1. Executive Summary

This ecosystem bridges two specialized inventory domains:
1. **PartDB**: Engineering-level component database managing electronic parts, LEGO elements, technical specifications, CAD footprints, lot numbers, data sheets, and component categories.
2. **ModernWMS**: Warehouse Management System managing standard product units (`spu`), stock keeping units (`sku`), advance shipping notices (`asn`), stock sorting, put-aways, multi-location inventory, and role-based permissions.

Current subcomponents include:
- **TUI & CLI Tools**: Full-featured curses/ANSI terminal suites supporting keyboard, touchscreen gestures, tablet numpads, dual themes, and database operations.
- **Sync Engine & API**: Real-time SQLite sync daemon running on port `8082`, exposing REST endpoints, Prometheus `/metrics`, and a web control center.
- **Multi-Channel Gateway**: Web proxy on port `7681`, ttyd terminal engine on `7682`, and Telnet daemon on `2323` for rugged barcode scanners.
- **Android APK Package**: Standalone WebView app wrapper for Android warehouse tablets.

---

## 2. Core Entities & Data Dictionary

### Part & Product Model
* **Part ID (`partdb_id` / `spu_id` / `sku_id`)**: The primary integer identifier preserved across both systems.
* **Specification Code (`spec_code` / `spu_name` / `sku_name`)**: The human-readable name or part number (e.g. `2780`, `52107`, `3705`).
* **Commodity Code (`spu_code` / `sku_code` / `mfg_pn`)**: The manufacturer product number or IPN.
* **Category**: Classification hierarchy (e.g., `Technic Pins`, `Beams`, `Axles`, `Microcontrollers`).
* **Stock Quantity (`total_quantity` / `stock.qty`)**: Consolidated physical inventory count on hand at warehouse location `KCLEGO`.

### User & Security Model
* **User Roles**:
  - `Admin` (User Num: `7354`): Full system privileges, configuration, and security control.
  - `Picker` / `Operator` (User Num: `10932`): Warehouse sorting, ASN receipts, stock counts.
  - `ViewOnly` (User Num: `viewonly`): Read-only catalog browsing.
* **Authentication**:
  - ModernWMS: MD5 hash (`auth_string`).
  - PartDB: Symfony / Bcrypt password hashing.
  - Sync API: PBKDF2-HMAC-SHA256 with 100,000 iterations & 16-byte random salt.
* **Forced Password Reset**: `user_security.must_change_pw = 1` forces users with temporary passwords to choose a new password upon first login.

---

## 3. Operational Flows

### A. Stock Receiving (ASN / Notice on Arrival)
1. Operator scans barcode or enters Part Name + Quantity.
2. System generates unique ticket: `ASN` + `YYYYMMDDHHMMSS`.
3. Records created in ModernWMS `asn` (status `4` = Sorted) and `asnsort`.
4. `stock.qty` is atomically incremented at location `1` (`KCLEGO`).
5. Audit log event recorded with timestamp and operator ID.

### B. Real-Time Synchronization
1. Sync Engine queries PartDB SQLite database (`app.db`) for all parts, categories, and lots.
2. Formats payload with timestamps and executes synchronization logic inside ModernWMS container (`wms.db`).
3. Updates `spu`, `sku`, `category`, and calculates total inventory quantities.
4. Updates Prometheus counters (`partdb_sync_active_parts`, `partdb_sync_total_stock_qty`, etc.).

---

## 4. Key Architectural Goals for a New Unified App

When developing a unified Next.js/React/FastAPI application using this context:
1. **Single Pane of Glass**: Merge PartDB component specifications with ModernWMS warehouse operations into a single modern UI.
2. **Offline-First & Fast Barcode Scanning**: Native camera scanning (HTML5 QR/Barcode Scanner) and hardware wedge scanner support.
3. **Responsive Tablet / Mobile First**: Clean touch-friendly interface, on-screen numpads for glove-wearing warehouse workers.
4. **Audit Logging & Security**: Unified authentication, JWT/session management, and granular activity logging.
5. **Real-time Live Updates**: WebSockets or SSE for instant stock updates across all active client screens.
