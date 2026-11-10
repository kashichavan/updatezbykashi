"""Remove invented details from career-board ("Startup") jobs.

The old adapter replaced each real posting's JD with a one-line placeholder
that included a made-up "HR Contact Helpline" phone number per company (the
job page shows any number found in the text as the HR contact), and invented
salary labels. This strips those sentences and labels; the next ingestion
cycle replaces the placeholder with the employer's real JD.
"""
import re

from django.db import migrations

HELPLINE = re.compile(r"\s*HR Contact Helpline:\s*[+\d][\d\s\-]{8,}\d\.?")


def scrub(apps, schema_editor):
    JobPosting = apps.get_model("requirements", "JobPosting")
    for job in JobPosting.objects.filter(description__contains="HR Contact Helpline"):
        job.description = HELPLINE.sub("", job.description).strip()
        job.save(update_fields=["description"])
    JobPosting.objects.filter(stipend_salary__startswith="Startup Package").update(stipend_salary="Not disclosed")


class Migration(migrations.Migration):
    dependencies = [
        ("requirements", "0025_close_fabricated_naukri_jobs"),
    ]

    operations = [
        migrations.RunPython(scrub, migrations.RunPython.noop),
    ]
