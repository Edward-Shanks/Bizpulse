#!/usr/bin/env python3
"""
Apply RBAC fields to the MAIN production database 'bizpulse'.
Run this ONLY when you are ready to add role/access to users in production.
Uses the same logic as add_user_rbac_fields.py with --target-db bizpulse.
"""
import subprocess
import sys
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    add_rbac = os.path.join(script_dir, "add_user_rbac_fields.py")
    print("=" * 70)
    print("Apply RBAC to MAIN DB: bizpulse")
    print("=" * 70)
    print("This will add role and access fields to bizpulse.users.")
    r = subprocess.run([sys.executable, add_rbac, "--target-db", "bizpulse"])
    sys.exit(r.returncode)

if __name__ == "__main__":
    main()
