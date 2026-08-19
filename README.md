# ModernWMS & PartDB Unified Ecosystem

A multi-channel, real-time inventory and warehouse management platform that bridges **PartDB** (component cataloging & engineering specs) and **ModernWMS** (warehouse operations, logistics & ASN tracking).

Includes full CLI suites, touch tablet kiosks, Telnet scanner daemons, REST API endpoints, Prometheus observability, and ready-to-use context prompts for building custom applications in **[Google AI Studio](https://aistudio.google.com)**.

---

## 📁 Repository Structure

```
.
├── apps/
│   ├── cli/                     # CLI & TUI Management Tools
│   │   ├── modernwms_tui.py     # Interactive Terminal & Touch Control Suite
│   │   ├── user_manager.py      # Dual-DB User & Security Manager
│   │   ├── receive_stock.py     # ModernWMS ASN Stock Receiving CLI
│   │   ├── reset_modernwms_password.py # Password reset & temp password generator
│   │   └── modernwms_backup.py  # SQLite automated database backup utility
│   ├── gateway/                 # Multi-Channel Access Gateway
│   │   ├── web_proxy.py         # HTTP & WebSocket proxy (PWA & APK distributor)
│   │   ├── telnet_server.py     # RFC 854 Telnet daemon for barcode scanners
│   │   ├── start_webtui.sh      # Gateway process launcher
│   │   └── kiosk_index.html     # Touch kiosk web UI
│   └── mobile/                  # Android Wrapper & Kiosk APK
│       ├── build_apk.py         # APK build automation script
│       └── AndroidManifest.xml  # Manifest for Android WebView wrapper
│
├── services/
│   └── sync-service/            # Real-Time Sync Engine & Dashboard
│       ├── sync_service.py      # Core daemon, REST API & Web Dashboard
│       ├── set_password.py      # PBKDF2 credential management utility
│       ├── Dockerfile           # Sync container definition
│       └── docker-compose.yml   # Sync service Docker Compose stack
│
├── deploy/
│   ├── docker/                  # Docker Compose stacks
│   │   ├── partdb/              # PartDB container stack
│   │   ├── monitoring/          # Prometheus & Grafana monitoring stack
│   │   └── npm/                 # Nginx Proxy Manager stack
│   └── systemd/                 # Production systemd service unit files
│       ├── modernwms-webtui.service
│       └── partdb-modernwms-sync.service
│
├── docs/                        # Complete Documentation Suite
│   ├── ARCHITECTURE.md          # Architecture & data flow diagrams
│   ├── API_REFERENCE.md         # REST API endpoints & metrics reference
│   ├── DATABASE_SCHEMAS.md      # PartDB & ModernWMS SQLite schemas
│   ├── DEPLOYMENT_GUIDE.md      # Setup, systemd & Docker deployment
│   ├── AI_STUDIO_CONTEXT.md     # Domain knowledge packet for AI Studio
│   └── AI_STUDIO_MASTER_PROMPT.md # Ready-to-copy Master Prompt for Gemini
│
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── install.sh                   # Global CLI setup & symlink script
```

---

## ⚡ Quick Start

### 1. Install CLI Tools & Symlinks
```bash
git clone <repo-url> modernwms-partdb-suite
cd modernwms-partdb-suite
chmod +x install.sh
./install.sh
```

### 2. Available Terminal Commands
* `modernwms`: Launch the Touch & Keyboard Terminal Control Suite.
* `manage-users`: Manage users, assign roles, and issue temporary passwords across both databases.
* `receive-stock <part_name> <qty>`: Instantly receive stock with an official ASN ticket.
* `reset-modernwms-password <username>`: Reset passwords with forced first-login change.

### 3. Start Multi-Channel Gateways (Web, Touch Kiosk & Telnet)
```bash
bash apps/gateway/start_webtui.sh
```
* **Web TUI & PWA**: `http://localhost:7681`
* **Telnet (Barcode Scanners / PuTTY)**: `telnet localhost 2323`

### 4. Start Sync API & Observability Dashboard
```bash
python3 services/sync-service/sync_service.py
```
* **Live Control Dashboard**: `http://localhost:8082`
* **Prometheus Metrics**: `http://localhost:8082/metrics`

---

## 🤖 Building Apps with Google AI Studio (`aistudio.google.com`)

To build a modern fullstack web or mobile app (e.g. Next.js + React + Tailwind + FastAPI):
1. Open [Google AI Studio](https://aistudio.google.com).
2. Attach or paste the contents of [`docs/AI_STUDIO_CONTEXT.md`](docs/AI_STUDIO_CONTEXT.md) as system instructions.
3. Paste the prompt from [`docs/AI_STUDIO_MASTER_PROMPT.md`](docs/AI_STUDIO_MASTER_PROMPT.md).
4. Prompt Gemini to generate your custom app components, database migrations, or native mobile interfaces!

---

## 🔒 Security & Roles

| Role | User ID / Num | Default Access | Description |
| :--- | :--- | :--- | :--- |
| **Admin** | `7354` / `admin` | Full Read/Write | System configuration, database sync, user security |
| **Picker / Operator** | `10932` | Inventory Operations | Warehouse picking, sorting, ASN receipts |
| **View-Only** | `viewonly` | Read-Only | Safe inventory lookup without modification rights |

---

## 📜 License
MIT License. Built for enterprise warehouse operations and electronic engineering part cataloging.
