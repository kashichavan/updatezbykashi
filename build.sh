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

# Auto-create production owner account, Software & Tech category, and seed guide articles & blog
python requirements/seed_prod.py || true
python manage.py seed_blog || true
python manage.py seed_deep_blogs || true

# Auto-clean legacy database duplicates & normalize company names
python manage.py shell -c "import requirements.jobdexo_service as j; j.cleanup_all_database_duplicates()" || true

# Auto-sync newest verified off-campus opportunities from Jobdexo
python manage.py sync_jobdexo --count 5 || true

