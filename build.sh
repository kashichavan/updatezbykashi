#!/usr/bin/env bash
# exit on error for packaging steps
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput

# Run migrations with resilient retry loop for Render/Supabase cloud databases
echo "==> Running database migrations..."
for i in {1..5}; do
  if python manage.py migrate --noinput; then
    echo "==> Migrations applied successfully."
    break
  else
    echo "==> Migration attempt $i failed. Retrying in 3s..."
    sleep 3
  fi
done

# Auto-restore full snapshot if fresh empty database
python manage.py shell -c "
from requirements.models import JobPosting
from django.core.management import call_command
if JobPosting.objects.count() == 0:
    print('==> Fresh database detected! Restoring latest full snapshot backup (442 objects)...')
    try:
        call_command('loaddata', 'backups/kashii_full_snapshot_latest.json')
        print('==> Full backup snapshot restored successfully into new database!')
    except Exception as e:
        print('==> Snapshot restore notice:', e)
" || true

# Auto-create production owner account, Software & Tech category, and seed guide articles & blog
python requirements/seed_prod.py || true
python manage.py seed_blog || true
python manage.py seed_deep_blogs || true

# Auto-clean legacy database duplicates & normalize company names
python manage.py shell -c "import requirements.jobdexo_service as j; j.cleanup_all_database_duplicates()" || true

# Auto-sync newest verified off-campus opportunities from Jobdexo
python manage.py sync_jobdexo --count 5 || true

