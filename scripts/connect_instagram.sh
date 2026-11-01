#!/usr/bin/env bash
# One-shot Instagram setup: paste the token into the dialog, the rest is automatic.
set -euo pipefail
cd "$(dirname "$0")/.."

ask() {
  osascript -e 'on run argv' \
    -e 'text returned of (display dialog (item 1 of argv) default answer "" with hidden answer with title "KashiiUpdatez Instagram" giving up after 1800)' \
    -e 'end run' "$1"
}

open "https://developers.facebook.com/apps/1063466270010969/"

TOKEN="$(ask 'Instagram > API setup with Instagram login > Generate access tokens > Add account. Log in as @ikashii_07, then paste the IGAA... token here.')"
[ -n "$TOKEN" ] || { echo "No token entered."; exit 1; }
SECRET="$(ask 'Business login settings: paste the Instagram app secret for the 60-day upgrade. Leave empty to skip.')"

printf '%s\n%s\n' "$TOKEN" "$SECRET" | env/bin/python manage.py setup_instagram_token --from-stdin
unset TOKEN SECRET

echo "Waiting for production to be ready..."
for _ in $(seq 1 40); do
  if env/bin/python manage.py publish_test_story --dry-run; then
    env/bin/python manage.py publish_test_story
    exit 0
  fi
  sleep 30
done
echo "Production was not ready after 20 minutes. Nothing was published."
exit 1
