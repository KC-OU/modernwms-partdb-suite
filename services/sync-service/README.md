# PartDB ➔ ModernWMS Sync Service & Observability Dashboard

Real-time synchronization engine, dark-mode observability control center, and REST API bridging PartDB and ModernWMS.

## Features

- **Bidirectional Synchronization**: Automatically reflects PartDB parts, categories, and stock into ModernWMS SPUs, SKUs, and inventory.
- **Observability Dashboard**: Real-time dark-mode web UI at `http://localhost:8082`.
- **REST API**: Full suite of endpoints for status, parts query, manual sync trigger, link persistence, and password management.
- **Prometheus Metrics**: Exposes `/metrics` for scraping by Prometheus and visualizing in Grafana.
- **PBKDF2 Password Security**: HTTP Basic Authentication secured via 100,000 PBKDF2-HMAC-SHA256 hashing rounds with 16-byte random salts.

## Running the Sync Service

### Directly with Python:
```bash
python3 services/sync-service/sync_service.py
```

### With Docker Compose:
```bash
cd services/sync-service
docker compose up -d
```

### Updating Admin Password:
```bash
python3 services/sync-service/set_password.py
```
