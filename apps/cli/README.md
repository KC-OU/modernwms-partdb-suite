# CLI & Terminal Tools

This directory contains standalone terminal utilities and interactive TUI applications.

## Files

| File | Description | Global CLI Alias |
| :--- | :--- | :--- |
| `modernwms_tui.py` | Full-featured Touch & Terminal Control Suite for warehouse operations | `modernwms`, `modernwms-tui`, `partdb-tui` |
| `user_manager.py` | Dual-database user management, password resets, and forced password changes | `manage-users`, `user-manager` |
| `receive_stock.py` | ModernWMS ASN (Notice on Arrival) stock receiving script | `receive-stock` |
| `reset_modernwms_password.py` | Command-line password reset and temp credential generator | `reset-modernwms-password` |
| `modernwms_backup.py` | Automated SQLite backup extractor for ModernWMS database | - |

## Usage Examples

```bash
# Run interactive control suite
python3 apps/cli/modernwms_tui.py

# List all registered users across both databases
python3 apps/cli/user_manager.py --list

# Generate a temporary password for user 7354 with forced change
python3 apps/cli/reset_modernwms_password.py --temp 7354

# Receive 5 units of part 2780 into stock via ASN
python3 apps/cli/receive_stock.py 2780 5
```
