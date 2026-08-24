#!/usr/bin/env python3
"""
Automated 12-Hour Database Backup Daemon for Kashii Updatez
Runs continuously in the background and takes a timestamped backup every 12 hours.
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXEC = BASE_DIR / "env" / "bin" / "python3"
INTERVAL_SECONDS = 12 * 60 * 60  # 12 hours

def run_backup():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled 12-hour backup...")
    try:
        res = subprocess.run(
            [str(PYTHON_EXEC), str(BASE_DIR / "manage.py"), "auto_backup"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=True
        )
        print(res.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup Error: {e.stderr.strip()}", file=sys.stderr)

def main():
    print(f"=== Kashii Updatez 12-Hour Auto Backup Service Started ===")
    print(f"Project Directory: {BASE_DIR}")
    print(f"Backup Interval: 12 Hours ({INTERVAL_SECONDS} seconds)")
    
    # Run initial backup on start
    run_backup()
    
    while True:
        try:
            time.sleep(INTERVAL_SECONDS)
            run_backup()
        except KeyboardInterrupt:
            print("\nAuto Backup daemon stopped by user.")
            break
        except Exception as ex:
            print(f"Unexpected error: {ex}", file=sys.stderr)
            time.sleep(60)

if __name__ == "__main__":
    main()
