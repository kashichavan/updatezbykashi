#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Auto-create production owner account, Software & Tech category, and seed guide articles
python requirements/seed_prod.py
