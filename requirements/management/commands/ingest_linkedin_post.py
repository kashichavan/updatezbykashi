import sys
from django.core.management.base import BaseCommand
from requirements.linkedin_service import (
    scrape_linkedin_url,
    parse_linkedin_content,
    validate_linkedin_lead,
    publish_linkedin_lead
)


class Command(BaseCommand):
    help = "Scrape, parse, validate, and pass/publish LinkedIn job requirement & employee referral posts."

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, default='', help='LinkedIn post or job URL')
        parser.add_argument('--text', type=str, default='', help='Raw text snippet or content of the LinkedIn post')
        parser.add_argument('--file', type=str, default='', help='Path to file containing raw LinkedIn post text')
        parser.add_argument('--referral', action='store_true', default=False, help='Force classification as Employee Referral')
        parser.add_argument('--referrer-name', type=str, default='', help='Name of the employee/recruiter offering referral')
        parser.add_argument('--referrer-linkedin', type=str, default='', help='LinkedIn profile URL of referrer')
        parser.add_argument('--publish', action='store_true', default=False, help='Publish directly to database if validation passes')

    def handle(self, *args, **options):
        url = options['url'].strip()
        raw_text = options['text'].strip()
        file_path = options['file'].strip()
        force_referral = options['referral']
        referrer_name = options['referrer_name'].strip()
        referrer_linkedin = options['referrer_linkedin'].strip()
        do_publish = options['publish']

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read().strip()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to read text file: {e}"))
                sys.exit(1)

        if not url and not raw_text:
            self.stderr.write(self.style.ERROR("Error: Provide at least --url or --text / --file."))
            sys.exit(1)

        self.stdout.write(self.style.NOTICE("🔍 Analyzing LinkedIn Post..."))

        # If URL given without text, scrape public metadata
        if url and not raw_text:
            self.stdout.write(f"Scraping metadata from: {url}")
            scrape_res = scrape_linkedin_url(url)
            if scrape_res.get('raw_text'):
                raw_text = scrape_res['raw_text']
                self.stdout.write(self.style.SUCCESS("✓ Scraped public OpenGraph metadata from LinkedIn."))
            elif not scrape_res.get('success'):
                self.stdout.write(self.style.WARNING(f"Note: {scrape_res.get('error', 'Could not scrape page directly.')}"))

        # Parse content
        parsed = parse_linkedin_content(
            raw_text=raw_text,
            source_url=url,
            force_referral=force_referral if force_referral else None,
            referrer_name=referrer_name,
            referrer_linkedin=referrer_linkedin
        )

        # Validate
        val = validate_linkedin_lead(parsed)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"VALIDATION SCORE: {val['score']}/100 — STATUS: {val['status']}"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Company:               {parsed.get('company')}")
        self.stdout.write(f"Role Title:            {parsed.get('title')}")
        self.stdout.write(f"Opportunity Type:      {'🤝 Employee Referral' if parsed.get('is_referral') else '💼 Job Requirement'}")
        self.stdout.write(f"Location:              {parsed.get('location')} (Remote: {parsed.get('is_remote')})")
        self.stdout.write(f"Salary / Stipend:      {parsed.get('stipend_salary')}")
        self.stdout.write(f"Skills Required:       {parsed.get('skills_required')}")
        self.stdout.write(f"Apply / Contact:       {parsed.get('apply_url')}")
        if parsed.get('is_referral'):
            self.stdout.write(f"Referrer Mention:      {parsed.get('referrer_name') or 'Not specified'}")
            self.stdout.write(f"Referrer LinkedIn:     {parsed.get('referrer_linkedin') or 'Not specified'}")
            self.stdout.write(f"Referral Instructions: {parsed.get('referral_instructions')}")
        self.stdout.write("-" * 60)

        self.stdout.write(self.style.NOTICE("Quality Checklist:"))
        for c in val.get('checks', []):
            icon = self.style.SUCCESS("✓") if c['passed'] else self.style.ERROR("✗")
            self.stdout.write(f"  {icon} {c['rule']}: {c['detail']} (+{c['points']} pts)")
        self.stdout.write("=" * 60)

        if not val['is_valid'] and do_publish:
            self.stdout.write(self.style.WARNING("⚠️ Lead did not meet minimum 70-point validation bar. Review fields before publishing."))

        if do_publish:
            job = publish_linkedin_lead(parsed, posted_by_user="CLI LinkedIn Ingestor")
            self.stdout.write(self.style.SUCCESS(f"\n🎉 PASSED & PUBLISHED! Created Job #{job.id}: {job.title} at {job.company_name}"))
            self.stdout.write(self.style.SUCCESS(f"URL: {job.get_absolute_url()}"))
        else:
            self.stdout.write(self.style.NOTICE("\nDry run complete. Use --publish to pass and commit directly to the live pipeline."))
