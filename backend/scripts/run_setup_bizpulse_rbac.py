#!/usr/bin/env python3
"""
One-shot setup for bizpulse_rbac:
1. Copy all collections from bizpulse → bizpulse_rbac (read-only from bizpulse)
2. Add RBAC fields to users in bizpulse_rbac

Production DB 'bizpulse' is never modified.
After this, set DB_NAME=bizpulse_rbac and use only bizpulse_rbac for read/write.
"""
import asyncio
import subprocess
import sys
import os

# Run from backend/ so scripts are in ./scripts
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BACKEND_DIR)


def run_script(name: str, *args) -> bool:
    cmd = [sys.executable, os.path.join("scripts", name)] + list(args)
    print(f"\n▶ Running: {' '.join(cmd)}\n")
    r = subprocess.run(cmd)
    return r.returncode == 0


def main():
    print("=" * 70)
    print("Setup bizpulse_rbac (copy + RBAC)")
    print("=" * 70)
    if not run_script("copy_bizpulse_to_bizpulse_rbac.py"):
        print("❌ Copy failed. Aborting.")
        sys.exit(1)
    if not run_script("add_user_rbac_fields.py", "--target-db", "bizpulse_rbac"):
        print("❌ Add RBAC failed. Aborting.")
        sys.exit(1)
    print("\n✅ Setup complete. Set DB_NAME=bizpulse_rbac in .env to use it.")


if __name__ == "__main__":
    main()
