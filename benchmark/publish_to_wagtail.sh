#!/usr/bin/env bash
#
# Publish post 11 (EN + PT) to tech.bilouro.com via the Lightsail VM.
#
# Steps:
#   1. scp the 2 .md + 2 .png to /tmp/fastapi-post-11/ on the VM
#   2. ssh + manage.py import_posts → creates BlogPostPage drafts
#   3. ssh + manage.py shell → set go_live_at on both pages
#       - 11-en → 2026-06-10 09:00 Lisbon
#       - 11-pt → 2026-06-12 09:00 Lisbon
#   4. Wagtail's publish_scheduled cron on the VM publishes at go_live_at
#
# Authorized by user for this session.

set -euo pipefail

VM_USER=ubuntu
VM_HOST=3.251.103.83
VM_KEY=~/.ssh/lightsail-bilouro.pem
SSH="ssh -o StrictHostKeyChecking=no -i $VM_KEY ${VM_USER}@${VM_HOST}"
SCP="scp -o StrictHostKeyChecking=no -i $VM_KEY"

POSTS=/Users/victor/Documents/GitHub/linkedin/knowledge-base/posts
STAGING=/tmp/fastapi-post-11

echo "▶ Staging files on VM…"
$SSH "rm -rf $STAGING && mkdir -p $STAGING"

$SCP \
  "$POSTS/11-async-fastapi-measured-en.md" \
  "$POSTS/11-async-fastapi-measured-pt.md" \
  "$POSTS/11-async-fastapi-measured-en.png" \
  "$POSTS/11-async-fastapi-measured-pt.png" \
  "${VM_USER}@${VM_HOST}:${STAGING}/"

echo "▶ Importing into Wagtail…"
$SSH bash <<'REMOTE_IMPORT'
set -euo pipefail
sudo -u bilouro bash <<'INNER'
set -euo pipefail
cd /opt/bilouro/web
export $(grep -v ^# /etc/bilouro.env | xargs)
.venv/bin/python manage.py import_posts /tmp/fastapi-post-11 --parent-slug tech 2>&1 | tail -30
INNER
REMOTE_IMPORT

echo
echo "▶ Setting go_live_at on the two pages…"
$SSH bash <<'REMOTE_SCHEDULE'
set -euo pipefail
sudo -u bilouro bash <<'INNER'
set -euo pipefail
cd /opt/bilouro/web
export $(grep -v ^# /etc/bilouro.env | xargs)
.venv/bin/python manage.py shell <<'PY'
import zoneinfo
from datetime import datetime
from django.utils import timezone
from wagtail.models import Page

LISBON = zoneinfo.ZoneInfo("Europe/Lisbon")
schedule = {
    "11-async-fastapi-measured-en": datetime(2026, 6, 10, 9, 0, tzinfo=LISBON),
    "11-async-fastapi-measured-pt": datetime(2026, 6, 12, 9, 0, tzinfo=LISBON),
}

for slug, when in schedule.items():
    qs = Page.objects.filter(slug=slug)
    if not qs.exists():
        print(f"NOT FOUND: {slug}")
        continue
    page = qs.first()
    page.go_live_at = when.astimezone(zoneinfo.ZoneInfo("UTC"))
    page.expire_at = None
    # Save as a new revision; we don't publish now — let the scheduler do it.
    page.save()
    print(f"SET go_live_at={page.go_live_at.isoformat()}  slug={slug}  url={page.url}")
PY
INNER
REMOTE_SCHEDULE

echo
echo "✓ done — Wagtail will publish at the scheduled times."
echo "  EN → 2026-06-10 09:00 Lisbon (08:00 UTC)"
echo "  PT → 2026-06-12 09:00 Lisbon (08:00 UTC)"
