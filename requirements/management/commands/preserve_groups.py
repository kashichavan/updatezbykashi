from django.core.management.base import BaseCommand

from requirements.group_archive import (
    fetch_live_groups,
    load_archive_file,
    merge_archive,
    newest_group_time,
)


class Command(BaseCommand):
    help = "Add groups from the committed archive and the running site. Never changes an existing group."

    def add_arguments(self, parser):
        parser.add_argument('--no-live', action='store_true', help='Use the committed archive only')

    def handle(self, *args, **options):
        added = merge_archive(load_archive_file())
        self.stdout.write(f"Archive: added {added['groups']} groups, {added['jobs']} jobs.")

        if options['no_live']:
            return
        try:
            live = fetch_live_groups(newest_group_time())
        except Exception as exc:
            # The site being asleep or down must not stop a deploy, but it does
            # mean groups made since the last commit were not carried over.
            self.stderr.write(self.style.WARNING(f"Live group pull FAILED, recent groups may be missing: {exc}"))
            return
        added = merge_archive(live)
        self.stdout.write(self.style.SUCCESS(
            f"Live site: {len(live.get('groups') or [])} recent groups seen, "
            f"added {added['groups']} groups, {added['jobs']} jobs."
        ))
