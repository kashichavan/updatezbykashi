"""Close the hardcoded "fallback" Naukri postings.

The Naukri adapter used to publish a fixed list of made-up jobs (invented
descriptions, salaries and HR phone numbers) whenever Naukri's API failed.
Those rows are matched by their exact fallback apply URLs, which are Naukri
search pages rather than real postings, and closed so they leave the feed,
the sitemap and Google's job results. Real Naukri postings (job-listings-*
URLs) are untouched.
"""
from django.db import migrations

FABRICATED_URLS = [
    "https://www.naukri.com/accenture-qa-jobs",
    "https://www.naukri.com/amazon-operations-specialist-jobs",
    "https://www.naukri.com/cognizant-full-stack-developer-jobs",
    "https://www.naukri.com/deloitte-business-analyst-jobs",
    "https://www.naukri.com/freshworks-customer-success-jobs",
    "https://www.naukri.com/hcltech-linux-administrator-jobs",
    "https://www.naukri.com/infosys-python-developer-jobs",
    "https://www.naukri.com/ltts-embedded-engineer-jobs",
    "https://www.naukri.com/ola-electric-firmware-engineer-jobs",
    "https://www.naukri.com/phonepe-sdet-jobs",
    "https://www.naukri.com/razorpay-data-analyst-jobs",
    "https://www.naukri.com/reliance-jio-network-engineer-jobs",
    "https://www.naukri.com/swiggy-frontend-developer-jobs",
    "https://www.naukri.com/tcs-java-developer-jobs",
    "https://www.naukri.com/tech-mahindra-cyber-security-jobs",
    "https://www.naukri.com/unacademy-business-development-jobs",
    "https://www.naukri.com/wipro-devops-engineer-jobs",
    "https://www.naukri.com/zerodha-software-engineer-jobs",
    "https://www.naukri.com/zomato-mobile-app-developer-jobs",
]


def close_fabricated(apps, schema_editor):
    JobPosting = apps.get_model("requirements", "JobPosting")
    urls = FABRICATED_URLS + [u + "/" for u in FABRICATED_URLS]
    JobPosting.objects.filter(apply_url__in=urls).exclude(status="CLOSED").update(status="CLOSED")


class Migration(migrations.Migration):
    dependencies = [
        ("requirements", "0024_remove_guides_and_blog_tables"),
    ]

    operations = [
        migrations.RunPython(close_fabricated, migrations.RunPython.noop),
    ]
