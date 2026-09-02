import os
import sys
import time
import threading
import django

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reqpulse.settings')
django.setup()

from django.core.wsgi import get_wsgi_application
from wsgiref.simple_server import make_server
from django.contrib.auth.models import User
from requirements.models import JobPosting, JobGroup
from playwright.sync_api import sync_playwright

u = User.objects.filter(is_superuser=True).first()
if not u:
    u = User.objects.create_superuser('admin_test', 'admin@example.com', 'KashiUpdatez@2026')
else:
    u.set_password('KashiUpdatez@2026')
    u.is_staff = True
    u.is_superuser = True
    u.save()

job = JobPosting.objects.filter(status='ACTIVE').first()
group = JobGroup.objects.first()

print(f"Target Job: #{job.id} - {job.title} | Destination Group: #{group.id} - {group.name}")

# Start WSGI Server
app = get_wsgi_application()
httpd = make_server('127.0.0.1', 8897, app)
server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
server_thread.start()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # 1. Login via native form navigation to establish full server session
    print("1. Opening /owner/ ...")
    page.goto("http://127.0.0.1:8897/owner/", wait_until="networkidle")

    if page.locator("#ownerLoginView").is_visible():
        print("2. Submitting login credentials...")
        page.fill("#ownerUser", u.username)
        page.fill("#ownerPass", "KashiUpdatez@2026")
        with page.expect_navigation():
            page.click("#formOwnerLogin button[type='submit']")
        print("Navigation finished!")

    # 2. Wait for stable dashboard state
    page.wait_for_selector("#ownerDashboardView", state="visible", timeout=15000)
    print("✅ Dashboard visible and ready!")

    # 3. Click Move button on target job
    print(f"3. Clicking Move button for Job #{job.id}...")
    move_btn = page.locator(f".btn-pipeline-move-job[data-id='{job.id}']").first
    if not move_btn.is_visible():
        move_btn = page.locator(".btn-pipeline-move-job").first

    move_btn.click()
    page.wait_for_timeout(1000)

    # 4. Verify Move Modal
    modal = page.locator("#moveRequirementsModal")
    assert modal.is_visible(), "Modal should be visible after clicking move button!"
    print("✅ Move Requirements Modal is OPEN and visible!")

    # 5. Check prefilled Job ID
    job_val = page.input_value("#manualJobIdsInput")
    print(f"Prefilled Job ID: '{job_val}'")
    assert str(job.id) in job_val

    # 6. Wait for destination group option in select
    print(f"6. Waiting for option #{group.id} in destination select...")
    page.wait_for_selector(f"#moveToGroupSelect option[value='{group.id}']", state="attached", timeout=10000)
    page.select_option("#moveToGroupSelect", value=str(group.id))
    print(f"Selected destination group #{group.id} ({group.name})")

    # 7. Confirm Move
    print("7. Clicking 'Confirm Move ⇄' button...")
    page.click("#btnConfirmMove")
    page.wait_for_timeout(2000)

    # 8. Toast Verification
    toast = page.locator(".toast").first
    if toast.is_visible():
        print(f"Toast displayed: '{toast.inner_text().strip()}'")

    # 9. Database Verification
    group.refresh_from_db()
    is_in_group = group.jobs.filter(id=job.id).exists()
    print(f"8. Database check: Is Job #{job.id} inside Group #{group.id}? -> {is_in_group}")
    assert is_in_group, "Requirement must be in destination group!"

    print("\n=========================================================================")
    print("🎉 FULL PLAYWRIGHT HEADLESS UI MOVE TEST PASSED WITH 100% SUCCESS!")
    print("=========================================================================\n")
    browser.close()

