#!/usr/bin/env python3
"""
Enterprise Playwright Test Suite CLI Runner
Usage:
    python3 run_playwright_tests.py
    python3 run_playwright_tests.py --headed
    python3 run_playwright_tests.py --url http://127.0.0.1:8000
    python3 run_playwright_tests.py --module test_01_homepage.py
"""

import sys
import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Run Playwright UI Automation Tests for Kashii Updatez")
    parser.add_argument("--url", default="https://kashiiupdatez.online", help="Base URL to test (default: https://kashiiupdatez.online)")
    parser.add_argument("--headed", action="store_true", help="Run browser in visible headed mode")
    parser.add_argument("--slowmo", type=int, default=0, help="Slow down execution by N milliseconds")
    parser.add_argument("--module", default="", help="Specific test file or pattern (e.g. test_01_homepage.py)")
    parser.add_argument("--html", action="store_true", default=True, help="Generate HTML test report")
    
    args = parser.parse_args()

    os.environ["BASE_URL"] = args.url
    os.environ["HEADED"] = "1" if args.headed else "0"
    os.environ["SLOWMO"] = str(args.slowmo)

    test_target = f"tests_playwright/{args.module}" if args.module else "tests_playwright"
    report_path = "tests_playwright/reports/playwright_report.html"

    cmd = [
        sys.executable, "-m", "pytest",
        test_target,
        "-v",
        "-s",
        f"--html={report_path}",
        "--self-contained-html"
    ]

    print("=" * 70)
    print(f"🚀 Starting Kashii Updatez Playwright UI Automation Test Suite")
    print(f"   Target URL : {args.url}")
    print(f"   Mode       : {'Headed' if args.headed else 'Headless'}")
    print(f"   Scope      : {test_target}")
    print("=" * 70)

    result = subprocess.run(cmd)

    if os.path.exists(report_path):
        print(f"\n📊 HTML Report Generated: {os.path.abspath(report_path)}")

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
