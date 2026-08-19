#!/usr/bin/env python3
"""
ModernWMS & PartDB User & Password Management Script
Allows resetting passwords for any ModernWMS or PartDB user directly from host terminal,
generating random temporary passwords with forced first-login password changes.

Usage:
  reset-modernwms-password <username_or_id> [new_password]
  reset-modernwms-password --temp <username_or_id>
  reset-modernwms-password --list
"""

import sys
import os

# Import user manager engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/root/scripts")
import user_manager

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("ModernWMS & PartDB Terminal Password Reset Tool")
        print("Usage:")
        print("  reset-modernwms-password <username_or_id> [new_password]")
        print("  reset-modernwms-password --temp <username_or_id>   (Generates random temporary password)")
        print("  reset-modernwms-password --list                    (List all registered users)")
        sys.exit(0)

    if sys.argv[1] in ["-l", "--list"]:
        users = user_manager.list_all_users()
        print(f"\n{'SYSTEM':<11} | {'ID':<4} | {'USERNAME':<15} | {'ROLE / GROUP':<18} | {'STATUS':<9} | {'TEMP PW?':<9} | {'EMAIL'}")
        print("-" * 95)
        for u in users:
            status_str = "ACTIVE" if u['is_valid'] else "DISABLED"
            temp_str = "YES (FORCED)" if u['must_change_pw'] else "NO"
            print(f"{u['system']:<11} | {u['id']:<4} | {u['username']:<15} | {u['role']:<18} | {status_str:<9} | {temp_str:<9} | {u['email']}")
        print()
        sys.exit(0)

    is_temp = True
    username = ""
    new_password = None

    if sys.argv[1] in ["-t", "--temp"]:
        if len(sys.argv) < 3:
            print("Error: Missing username argument.")
            sys.exit(1)
        username = sys.argv[2]
        is_temp = True
    else:
        username = sys.argv[1]
        if len(sys.argv) >= 3:
            new_password = sys.argv[2]
            is_temp = False
        else:
            is_temp = True

    ok, msg, pwd = user_manager.reset_unified_password(username, new_password=new_password, is_temp=is_temp)
    if ok:
        print(f"✅ {msg}")
        if is_temp:
            print(f"🔑 Generated Temporary Password: {pwd}")
            print("⚠️  The user will be required to choose a new password upon their next login.")
        else:
            print(f"🔑 Password set to: {pwd}")
    else:
        print(f"❌ {msg}")
        print("\nAvailable registered users:")
        users = user_manager.list_all_users()
        for u in users:
            print(f" - [{u['system']}] ID #{u['id']}: {u['username']} ({u['role']})")

if __name__ == "__main__":
    main()
