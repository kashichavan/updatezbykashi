#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Auto-create production owner account, Software & Tech category, and seed guide articles & blog
python requirements/seed_prod.py
python manage.py seed_blog
python manage.py seed_deep_blogs

# Auto-sync newest verified off-campus opportunities from Jobdexo
python manage.py sync_jobdexo --count 5 || true

