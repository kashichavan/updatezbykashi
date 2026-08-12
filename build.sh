#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Auto-create production owner account & Software & Tech category upon deployment/restart
python manage.py shell -c "
from django.contrib.auth.models import User
from requirements.models import Category, JobPosting
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
import os

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

# Re-assign existing jobs to Software & Tech & remove obsolete categories
JobPosting.objects.all().update(category=sw_cat)
Category.objects.exclude(id=sw_cat.id).delete()

# 3. Ensure Default Active Connected Instagram Account & Automation Rule
from instaautomation.models import InstagramAccount, CommentAutomation
insta_acc, _ = InstagramAccount.objects.get_or_create(
    username='ikashii_07',
    defaults={
        'user': u,
        'instagram_user_id': '1699121034511579',
        'display_name': 'Kashii Official',
        'is_connected': True,
        'is_active': True,
        'access_token': 'manual_owner_token_activated',
        'token_expires_at': timezone.now() + timedelta(days=365)
    }
)
insta_acc.is_connected = True
insta_acc.is_active = True
insta_acc.save()

if not CommentAutomation.objects.filter(instagram_account=insta_acc).exists():
    CommentAutomation.objects.create(
        instagram_account=insta_acc,
        user=u,
        name='Python Guide Reel Automation',
        keywords='python, guide, link, learn',
        comment_reply='Thanks! 👋 I just sent you a DM.',
        require_follow=True,
        dm_message='Hey {{username}} 👋 Make sure to follow @ikashii_07 and reply DONE to get the Python guide link!',
        confirmation_keyword='DONE',
        final_message='Awesome! 🎉 Here is your Python guide link: {{resource_url}}',
        resource_url='https://kashiiupdatez.online/category/software-tech/',
        is_active=True
    )

print('Production Owner account, Software & Tech category & Instagram Studio configured successfully.')
"
