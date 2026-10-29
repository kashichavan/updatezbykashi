#!/usr/bin/env bash
# exit on error for packaging steps
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput

# 1. Proactive SQLite self-healing integrity check
echo "==> Validating SQLite database integrity..."
python -c "
import sqlite3, os
db_path = 'db.sqlite3'
if os.path.exists(db_path):
    is_corrupt = False
    reason = ''
    try:
        if os.path.getsize(db_path) == 0:
            is_corrupt = True
            reason = '0-byte empty file'
        else:
            with open(db_path, 'rb') as f:
                header = f.read(16)
            if header != b'SQLite format 3\x00':
                is_corrupt = True
                reason = f'invalid header: {header}'
            else:
                conn = sqlite3.connect(db_path)
                res = conn.execute('PRAGMA quick_check;').fetchone()
                conn.close()
                if not res or res[0] != 'ok':
                    is_corrupt = True
                    reason = f'quick_check failed: {res}'
    except Exception as e:
        is_corrupt = True
        reason = str(e)

    if is_corrupt:
        print(f'==> [Self-Healing] Corrupted SQLite file detected ({reason})! Purging corrupt artifacts...')
        for ext in ['', '-wal', '-shm', '-journal']:
            f = db_path + ext
            if os.path.exists(f):
                try:
                    os.remove(f)
                    print(f'==> Removed corrupt artifact: {f}')
                except Exception as del_err:
                    print(f'==> Could not remove {f}: {del_err}')
    else:
        print('==> SQLite database header & quick_check: 100% HEALTHY.')
else:
    print('==> Clean environment: No db.sqlite3 found. Will initialize fresh.')
"

# 2. Run migrations with resilient retry loop
echo "==> Running database migrations..."
for i in {1..5}; do
  if python manage.py migrate --noinput; then
    echo "==> Migrations applied successfully."
    break
  else
    echo "==> Migration attempt $i failed. Retrying in 3s..."
    sleep 3
    if [ "$i" -eq 5 ]; then
      echo "==> Final migration retry: resetting database to clear any locks..."
      rm -f db.sqlite3*
      python manage.py migrate --noinput
    fi
  fi
done

# 3. Non-destructive sync of all groups and jobs from snapshot
python manage.py shell -c "
from requirements.models import JobPosting, JobGroup
from django.core.management import call_command
try:
    job_count = JobPosting.objects.count()
    group_count = JobGroup.objects.count()
    print(f'==> Database status: {job_count} jobs, {group_count} groups.')
    if job_count == 0 or group_count == 0:
        print('==> Restoring full snapshot backup...')
        call_command('restore_snapshot')
        print('==> Full backup snapshot restored successfully!')
    else:
        print('==> Merging snapshot to guarantee all historical and shared groups exist...')
        call_command('restore_snapshot')
        print(f'==> Group sync complete! Total groups preserved: {JobGroup.objects.count()}')
except Exception as e:
    print('==> Snapshot restore encountered error:', e)
    try:
        print('==> Retrying snapshot restoration...')
        call_command('restore_snapshot')
    except Exception as retry_err:
        print('==> Snapshot retry failed:', retry_err)
" || true

# 4. Auto-create production owner account, Software & Tech category, and seed guide articles & blog
python requirements/seed_prod.py || true
python manage.py seed_blog || true
python manage.py seed_deep_blogs || true
python manage.py seed_kdeldycke_blogs || true
python manage.py seed_starred_repo_blogs || true

# 5. Auto-clean legacy database duplicates & normalize company names
python manage.py shell -c "import requirements.jobdexo_service as j; j.cleanup_all_database_duplicates()" || true

# 6. Enforce strict monthly DB quota limits
python manage.py cleanup_db_quota || true

# 7. Auto-sync newest verified off-campus opportunities from Jobdexo
python manage.py sync_jobdexo --count 20 || true

# 8. Seed Indian Market Demonstration Projects Library (36 curated projects)
python manage.py seed_indian_projects || true




