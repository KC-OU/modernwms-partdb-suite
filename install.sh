#!/bin/bash
# ===============================================================================
# ModernWMS & PartDB Unified Suite Installer & CLI Symlink Manager
# ===============================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_DIR="$REPO_DIR/apps/cli"
BIN_DIR="/usr/local/bin"

echo "📦 Installing ModernWMS & PartDB CLI Tools to $BIN_DIR..."

chmod +x "$CLI_DIR"/*.py
chmod +x "$REPO_DIR/apps/gateway"/*.py "$REPO_DIR/apps/gateway"/*.sh
chmod +x "$REPO_DIR/services/sync-service"/*.py

# CLI Commands
ln -sf "$CLI_DIR/user_manager.py" "$BIN_DIR/manage-users"
ln -sf "$CLI_DIR/user_manager.py" "$BIN_DIR/user-manager"
ln -sf "$CLI_DIR/modernwms_tui.py" "$BIN_DIR/modernwms"
ln -sf "$CLI_DIR/modernwms_tui.py" "$BIN_DIR/modernwms-tui"
ln -sf "$CLI_DIR/modernwms_tui.py" "$BIN_DIR/partdb-tui"
ln -sf "$CLI_DIR/modernwms_tui.py" "$BIN_DIR/wms-tui"
ln -sf "$CLI_DIR/modernwms_tui.py" "$BIN_DIR/script-runner"
ln -sf "$CLI_DIR/receive_stock.py" "$BIN_DIR/receive-stock"
ln -sf "$CLI_DIR/reset_modernwms_password.py" "$BIN_DIR/reset-modernwms-password"

echo "✅ Installed CLI commands in $BIN_DIR:"
echo "   - modernwms (modernwms-tui / partdb-tui / wms-tui)"
echo "   - manage-users (user-manager)"
echo "   - receive-stock"
echo "   - reset-modernwms-password"
echo ""
echo "🚀 To run the Touch/Web/Telnet gateway: bash $REPO_DIR/apps/gateway/start_webtui.sh"
echo "🔄 To run the Sync API & Dashboard:     python3 $REPO_DIR/services/sync-service/sync_service.py"
