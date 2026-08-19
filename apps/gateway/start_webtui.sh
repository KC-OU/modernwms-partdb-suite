#!/bin/bash
# ===============================================================================
# ModernWMS & PartDB Multi-Channel Gateway Launcher
# Services:
#   - ttyd Terminal Engine (Port 7682) with clean touch kiosk (No SGR mouse noise)
#   - Gateway Web Proxy & PWA Server (Port 7681)
#   - Dedicated Telnet Daemon (Port 2323) for Barcode Scanners & PuTTY
# ===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$(cd "$SCRIPT_DIR/../cli" 2>/dev/null && pwd || echo "/root/scripts")"

TELNET_SCRIPT="${SCRIPT_DIR}/telnet_server.py"
KIOSK_HTML="${SCRIPT_DIR}/kiosk_index.html"
PROXY_SCRIPT="${SCRIPT_DIR}/web_proxy.py"
TUI_SCRIPT="${CLI_DIR}/modernwms_tui.py"

# Fallbacks if running legacy
[ ! -f "$TELNET_SCRIPT" ] && TELNET_SCRIPT="/root/scripts/telnet_server.py"
[ ! -f "$KIOSK_HTML" ] && KIOSK_HTML="/root/scripts/kiosk_index.html"
[ ! -f "$PROXY_SCRIPT" ] && PROXY_SCRIPT="/root/scripts/web_proxy.py"
[ ! -f "$TUI_SCRIPT" ] && TUI_SCRIPT="/root/scripts/modernwms_tui.py"

# 1. Start Dedicated Telnet Server on port 2323
python3 "$TELNET_SCRIPT" &
TELNET_PID=$!

# 2. Start ttyd on port 7682 (without SGR mouse mode to prevent escape sequence noise)
/usr/bin/ttyd -W -p 7682 -I "$KIOSK_HTML" -t fontSize=18 -t disableLeaveAlert=true python3 "$TUI_SCRIPT" &
TTYD_PID=$!

# 3. Start Gateway Web Proxy on port 7681 (Web, PWA, WebSocket proxy)
sleep 1
python3 "$PROXY_SCRIPT" &
PROXY_PID=$!

echo "🚀 All Multi-Channel Access Gateways Active:"
echo "   - Web App / PWA:  http://0.0.0.0:7681"
echo "   - Telnet Access:  telnet 0.0.0.0 2323"
echo "   - Local CLI:      modernwms / manage-users"

trap "kill $TELNET_PID $TTYD_PID $PROXY_PID 2>/dev/null" EXIT
wait -n $TELNET_PID $TTYD_PID $PROXY_PID
