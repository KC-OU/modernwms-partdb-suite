# Multi-Channel Access Gateway

This directory provides the multi-channel gateway enabling Web, Mobile PWA, Tablet Touch Kiosk, and Telnet access to the ModernWMS & PartDB ecosystem.

## Components

| Component | Port | Description |
| :--- | :--- | :--- |
| `web_proxy.py` | `7681` | Reverse proxy for WebTUI, serves `/manifest.json` for PWA and `/ModernWMS_Touch_Suite.apk` for 1-click download |
| `kiosk_index.html` | - | Touch kiosk web UI wrapper for ttyd terminal engine |
| `telnet_server.py` | `2323` | RFC 854 compliant Telnet daemon with PTY allocation for barcode scanners and PuTTY |
| `start_webtui.sh` | - | Process manager script that spawns telnet, ttyd, and proxy concurrently |

## Running the Gateway

```bash
bash apps/gateway/start_webtui.sh
```
