#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Auto-create production owner account upon deployment
python manage.py shell -c "
from django.contrib.auth.models import User
import os

username = os.environ.get('ADMIN_USERNAME', 'kashichavan7777')
email = os.environ.get('ADMIN_EMAIL', 'kashichavan7777@gmail.com')
password = os.environ.get('ADMIN_PASSWORD', 'kashichavan7777')

u, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
u.email = email
u.set_password(password)
u.is_staff = True
u.is_superuser = True
u.save()
print('Production Owner account created/updated successfully.')
"
