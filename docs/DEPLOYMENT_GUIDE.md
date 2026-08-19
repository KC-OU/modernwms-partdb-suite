# Deployment & Operations Guide

## 1. Prerequisites

* **Operating System**: Linux (Debian, Ubuntu, Arch Linux, Alpine, or RHEL)
* **Runtime**: Python 3.10+
* **Container Engine**: Docker & Docker Compose
* **Terminal Engine** (for WebTUI): `ttyd`

---

## 2. Fast Setup (Host Installation)

Clone or navigate into the repository root and run the setup script:

```bash
cd /root/modernwms-partdb-suite
chmod +x install.sh
./install.sh
```

This registers the global CLI aliases into `/usr/local/bin`:
- `modernwms` (or `modernwms-tui` / `partdb-tui`): Interactive Terminal Control Suite.
- `manage-users` (or `user-manager`): Unified dual-database user & password manager.
- `receive-stock`: Instant ASN notice on arrival stock receiving tool.
- `reset-modernwms-password`: Command-line password reset and temp credential generator.

---

## 3. Running Services via Systemd

Systemd unit files are located in `deploy/systemd/`:

1. **Copy unit files into systemd directory**:
```bash
cp deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
```

2. **Enable and start the services**:
```bash
# PartDB -> ModernWMS Sync Daemon & REST API
systemctl enable --now partdb-modernwms-sync.service

# Touch Web TUI & Multi-Channel Gateway
systemctl enable --now modernwms-webtui.service
```

3. **Check service status**:
```bash
systemctl status partdb-modernwms-sync.service
systemctl status modernwms-webtui.service
```

---

## 4. Running via Docker Compose

### PartDB Container:
```bash
cd deploy/docker/partdb
docker compose up -d
```
* Access PartDB web portal on port `8081` (e.g. `http://localhost:8081/en/`).

### PartDB -> ModernWMS Sync Service:
```bash
cd services/sync-service
docker compose up -d
```
* Access Sync API & Live Dashboard on port `8082`.

### Monitoring (Prometheus & Grafana):
```bash
cd deploy/docker/monitoring
docker compose up -d
```
* Prometheus: `http://localhost:9091`
* Grafana: `http://localhost:3000` (Default login: `admin` / `admin123`)

---

## 5. Network Port Allocation

| Port | Service | Protocol | Description |
| :--- | :--- | :--- | :--- |
| `80` | ModernWMS Web UI | HTTP | ModernWMS Web Application |
| `8081` | PartDB Web UI | HTTP | PartDB Component Management Portal |
| `8082` | Sync Dashboard & REST API | HTTP | Live Sync Engine, Metrics & API |
| `7681` | Gateway Web Proxy | HTTP/WS | Touch Suite PWA & Web Gateway |
| `7682` | ttyd Terminal Server | HTTP/WS | Raw terminal rendering engine |
| `2323` | Telnet Server | TCP (RFC 854) | Rugged scanners & PuTTY |
| `3000` | Grafana | HTTP | Observability Dashboards |
| `9091` | Prometheus | HTTP | Metrics Time-Series DB |
