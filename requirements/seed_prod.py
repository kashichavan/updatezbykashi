import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reqpulse.settings')
django.setup()

from django.contrib.auth.models import User
from requirements.models import Category, JobPosting

# 1. Ensure Owner Account
username = os.environ.get('ADMIN_USERNAME', 'kashichavan7777')
email = os.environ.get('ADMIN_EMAIL', 'kashichavan7777@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'kashichavan7777')

u, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
u.email = email
u.set_password(password)
u.is_staff = True
u.is_superuser = True
u.save()

# 2. Ensure Sole Active Category: Software & Tech
sw_cat, _ = Category.objects.get_or_create(
    slug='software-tech',
    defaults={
        'name': 'Software & Tech',
        'icon': 'code',
        'description': 'All software engineering, web development, internships, and technology opportunities.'
    }
)

JobPosting.objects.filter(category__isnull=True).update(category=sw_cat)


# 3. Comprehensive High-Value Guide Library with Downloadable PDFs from User Drive
PYTHON_DRIVE_FOLDER = "https://drive.google.com/drive/folders/1tULDwty-7eXsHh2jAAKCM2OK7YxYSuyp?usp=drive_link"
JAVA_DRIVE_FOLDER = "https://drive.google.com/drive/folders/1khZVS3OSY3EyVVOrRZi33QGchWI9ntM2?usp=drive_link"

print("\nProduction seeding completed successfully.")

