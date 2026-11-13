"""Fix JobPosting source_name defaults and cleanup misclassified Jobdexo jobs."""
from django.db import migrations, models
from django.db.models import Q


def cleanup_sources(apps, schema_editor):
    JobPosting = apps.get_model("requirements", "JobPosting")

    # 1. Real Jobdexo postings
    JobPosting.objects.filter(
        Q(source_url__icontains='jobdexo.com') | Q(apply_url__icontains='jobdexo.com')
    ).update(source_name='Jobdexo')

    # 2. Misclassified Naukri postings
    JobPosting.objects.filter(
        source_name='Jobdexo',
        apply_url__icontains='naukri.com'
    ).exclude(source_url__icontains='jobdexo.com').update(source_name='Naukri')

    # 3. Misclassified LinkedIn postings
    JobPosting.objects.filter(
        source_name='Jobdexo',
        apply_url__icontains='linkedin.com'
    ).exclude(source_url__icontains='jobdexo.com').update(source_name='LinkedIn')

    # 4. Misclassified Startup ATS postings
    startup_ats = ['lever.co', 'greenhouse.io', 'ashbyhq.com', 'workable.com']
    for ats in startup_ats:
        JobPosting.objects.filter(
            source_name='Jobdexo',
            apply_url__icontains=ats
        ).exclude(source_url__icontains='jobdexo.com').update(source_name='Startup')

    # 5. Misclassified Direct postings
    JobPosting.objects.filter(
        source_name='Jobdexo',
        source_url=''
    ).exclude(apply_url__icontains='jobdexo.com').update(source_name='Direct')


class Migration(migrations.Migration):
    dependencies = [
        ("requirements", "0028_reels_and_instagram"),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobposting',
            name='source_name',
            field=models.CharField(db_index=True, default='Direct', help_text='e.g. Jobdexo, Greenhouse, Lever, Ashby, PublicFeeds, Direct', max_length=100),
        ),
        migrations.RunPython(cleanup_sources, migrations.RunPython.noop),
    ]
