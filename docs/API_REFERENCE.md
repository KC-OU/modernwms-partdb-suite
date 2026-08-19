# Sync Service & REST API Reference

The Sync Service runs on port `8082` (by default) and provides real-time data synchronization between PartDB and ModernWMS, alongside an observability dashboard, Prometheus metrics exporter, and a RESTful API.

## Authentication

All `/api/*` modification endpoints (and web dashboard access) use standard **HTTP Basic Authentication**.
- **Algorithm**: PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt.
- **Default Credentials**: `admin` / `admin123` (configurable via `CREDENTIALS_FILE` or `set_password.py`).

---

## Endpoints

### 1. Service Status
* **URL**: `GET /api/status`
* **Description**: Returns real-time synchronization engine health, uptime, execution duration, and item counters.
* **Response**: `200 OK` (application/json)
```json
{
  "status": "Success",
  "last_sync_time": "2026-08-19T15:30:00.123456",
  "stats": {
    "synced_categories": 12,
    "synced_locations": 1,
    "synced_parts": 48,
    "synced_stock_records": 48,
    "total_stock_qty": 350,
    "last_duration_seconds": 0.045,
    "total_sync_count": 1420,
    "total_error_count": 0,
    "api_requests_total": 85
  },
  "history": [
    {
      "timestamp": "2026-08-19 15:30:00",
      "duration_ms": 45.2,
      "synced_parts": 48,
      "total_stock_qty": 350
    }
  ]
}
```

---

### 2. Synced Parts Matrix
* **URL**: `GET /api/parts`
* **Description**: Returns all synchronized parts from PartDB mapped with their corresponding ModernWMS attributes, stock quantities, and URLs.
* **Response**: `200 OK` (application/json)
```json
{
  "status": "success",
  "count": 48,
  "parts": [
    {
      "partdb_id": 202,
      "name": "52107",
      "spec_code": "52107",
      "spu_code": "52107",
      "mfg_pn": "52107",
      "ipn": "52107",
      "category_id": 3,
      "category_name": "Technic Pins",
      "total_quantity": 25,
      "partdb_link": "https://partdb.kierancollins.xyz/en/part/202",
      "modernwms_link": "https://modernwms.kierancollins.xyz/"
    }
  ]
}
```

---

### 3. Trigger Manual Sync
* **URL**: `POST /api/sync`
* **Description**: Forces an immediate bidirectional synchronization cycle between PartDB and ModernWMS.
* **Response**: `200 OK` (application/json)
```json
{
  "status": "success",
  "last_sync_time": "2026-08-19T15:31:00.000000",
  "duration_ms": 52.4,
  "stats": { ... }
}
```

---

### 4. Direct Password Reset API
* **URL**: `POST /api/reset-password`
* **Description**: Allows administrators to reset passwords for any ModernWMS user directly in the database.
* **Request Body**: (application/json or form-data)
```json
{
  "username": "admin",
  "new_password": "NewSecurePassword123!"
}
```
* **Response**: `200 OK` (application/json)
```json
{
  "status": "success",
  "message": "ModernWMS user 'admin' password successfully updated!"
}
```

---

### 5. Part Link Override API
* **URL**: `POST /api/part-link`
* **Description**: Persists manual link overrides for specific parts to custom PartDB or ModernWMS URLs.
* **Request Body**: (application/json)
```json
{
  "part_id": 202,
  "partdb_link": "https://partdb.kierancollins.xyz/en/part/202",
  "modernwms_link": "https://modernwms.kierancollins.xyz/spu/detail/202"
}
```
* **Response**: `200 OK` (application/json)
```json
{
  "status": "success",
  "message": "Links saved for Part ID 202"
}
```

---

### 6. Prometheus Metrics Exporter
* **URL**: `GET /metrics`
* **Description**: Exposes OpenMetrics / Prometheus formatted telemetry for Grafana.
* **Metrics Provided**:
  - `partdb_sync_active_parts` (Gauge)
  - `partdb_sync_total_stock_qty` (Gauge)
  - `partdb_sync_categories` (Gauge)
  - `partdb_sync_duration_seconds` (Gauge)
  - `partdb_sync_total_runs` (Counter)
  - `partdb_sync_errors_total` (Counter)
  - `partdb_sync_api_requests_total` (Counter)
  - `partdb_sync_uptime_seconds` (Gauge)
