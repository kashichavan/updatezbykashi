import uuid
import re
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default="briefcase")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class JobPosting(models.Model):
    JOB_TYPE_CHOICES = [
        ('INTERNSHIP', 'Internship'),
        ('FULL_TIME', 'Full-Time Job'),
        ('PART_TIME', 'Part-Time Job'),
        ('FREELANCE', 'Freelance / Contract'),
        ('CAMPUS', 'Campus Drive'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active (Accepting Applications)'),
        ('EXPIRED', 'Deactivated / Expired (7-Day Auto-Closed)'),
        ('CLOSED', 'Manually Closed'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    title = models.CharField(max_length=200, help_text="e.g. Software Engineer Intern - Summer 2026")
    company_name = models.CharField(max_length=150, help_text="e.g. Stripe, Vercel, Microsoft")
    company_logo_icon = models.CharField(max_length=50, default="building")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='job_postings')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='INTERNSHIP')
    stipend_salary = models.CharField(max_length=100, help_text="e.g. $2,500/mo or $85,000/yr")
    location = models.CharField(max_length=150, default="Remote")
    is_remote = models.BooleanField(default=True)
    skills_required = models.TextField(default="Problem Solving, Software Engineering", help_text="Comma-separated skills e.g. Python, React, SQL")
    
    apply_url = models.URLField(max_length=500, blank=True, null=True, help_text="Official external application link")
    allow_direct_apply = models.BooleanField(default=True)

    description = models.TextField(help_text="Detailed job description and responsibilities")
    eligibility = models.TextField(blank=True, default="Open to all students")
    selection_process = models.TextField(
        blank=True,
        default="",
        help_text="Step-by-step interview selection rounds e.g. Round 1: Online Aptitude -> Round 2: Technical Interview -> Round 3: HR"
    )
    study_materials = models.JSONField(
        default=list,
        blank=True,
        help_text="List of free study material links with title, desc, and url"
    )
    
    posted_by = models.CharField(max_length=100, blank=True, default="Kashii Updatez Admin")
    poster_email = models.EmailField(blank=True, default="admin@kashiiupdatez.com")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    # ── LinkedIn & Employee Referral Metadata ──
    is_referral = models.BooleanField(default=False, db_index=True, help_text="True if this is an employee referral opportunity")
    referrer_name = models.CharField(max_length=150, blank=True, default="", help_text="Name of the employee/recruiter offering referral or posting on LinkedIn")
    referrer_linkedin = models.URLField(max_length=500, blank=True, default="", help_text="LinkedIn profile URL of the referrer/poster")
    referral_instructions = models.TextField(blank=True, default="", help_text="Instructions on how to get referred e.g. Email resume with Job ID to...")
    
    # ── India-Wide Multi-Source Aggregation & Last-Hour Discovery Fields ──
    PRECISION_CHOICES = [
        ('EXACT_TIMESTAMP', 'Exact Timestamp (Hour & Minute)'),
        ('APPROXIMATE_TIME', 'Approximate Timestamp (Relative)'),
        ('DATE_ONLY', 'Date Only (Day Level)'),
        ('UNKNOWN', 'Unknown / Not Provided'),
    ]
    DOMAIN_CHOICES = [
        ('TECHNICAL', 'Technical / Software / Data / Cloud / AI'),
        ('NON_TECHNICAL', 'Non-Technical / Business / Marketing / HR / Operations'),
    ]
    EXP_TIER_CHOICES = [
        ('INTERNSHIP', 'Internship / Student'),
        ('FRESHER', 'Fresher / 0–1 Years'),
        ('EARLY_CAREER', '1–3 Years Experience'),
        ('MID_LEVEL', '3–5 Years Experience'),
        ('SENIOR_LEVEL', '5+ Years / Senior Roles'),
    ]

    source_name = models.CharField(max_length=100, default='Jobdexo', db_index=True, help_text="e.g. Jobdexo, Greenhouse, Lever, Ashby, PublicFeeds")
    source_job_id = models.CharField(max_length=200, blank=True, default='', db_index=True)
    source_url = models.URLField(max_length=500, blank=True, default='', help_text="Original source portal link")
    source_published_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Original publication timestamp in UTC")
    source_updated_at = models.DateTimeField(null=True, blank=True, help_text="Original update timestamp in UTC")
    first_seen_at = models.DateTimeField(default=timezone.now, db_index=True, help_text="Timestamp when first discovered")
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True, help_text="Timestamp when most recently verified active")
    timestamp_precision = models.CharField(max_length=30, choices=PRECISION_CHOICES, default='DATE_ONLY', db_index=True)
    industry_domain = models.CharField(max_length=30, choices=DOMAIN_CHOICES, default='TECHNICAL', db_index=True)
    experience_tier = models.CharField(max_length=30, choices=EXP_TIER_CHOICES, default='FRESHER', db_index=True)
    normalized_city = models.CharField(max_length=100, default='Bengaluru', db_index=True, help_text="Normalized city e.g. Bengaluru, Hyderabad, Pune, Mumbai, Delhi NCR, Remote")
    ingestion_batch_id = models.CharField(max_length=64, blank=True, default='', db_index=True)

    # 7-Day Auto Expiration Policy
    created_at = models.DateTimeField(auto_now_add=True)
    posted_date = models.DateField(
        default=timezone.now,
        help_text="Date this requirement was posted (editable). Defaults to today."
    )
    deadline = models.DateTimeField(help_text="Automatically set to 7 days after posting")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posted_date', '-created_at']
        verbose_name = "Job Posting"
        verbose_name_plural = "Job Postings"
        indexes = [
            models.Index(fields=['status', '-posted_date', '-created_at']),
            models.Index(fields=['category', 'status', '-posted_date']),
            models.Index(fields=['uuid']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['company_name']),
            models.Index(fields=['status', 'deadline']),
            models.Index(fields=['industry_domain', 'status', '-source_published_at']),
            models.Index(fields=['normalized_city', 'status', '-source_published_at']),
            models.Index(fields=['source_name', 'source_job_id']),
            models.Index(fields=['-first_seen_at']),
        ]

    def save(self, *args, **kwargs):
        # 7-Day Auto-Expiry Policy to keep DB fresh & lean
        if not self.deadline:
            self.deadline = timezone.now() + timedelta(days=7)
        # Auto-set posted_date from today in Indian Standard Time if not set
        if not self.posted_date:
            self.posted_date = timezone.localtime(timezone.now()).date()
        super().save(*args, **kwargs)

    def is_expired(self):
        now = timezone.now()
        if self.status in ['CLOSED', 'EXPIRED']:
            return True
        if self.deadline and now > self.deadline:
            return True
        if self.created_at and (now - self.created_at).days >= 7:
            return True
        return False

    @property
    def clean_apply_url(self):
        url = (self.apply_url or '').strip()
        if not url:
            return ''
        if 'naukri.com/job-listings-' in url and '?' in url:
            # Strip fbclid, utm, and tracking query params that trigger Naukri app intent freeze
            url = url.split('?')[0]

        # Intercept mock Naukri IDs (9 digits like ...-221026006) that Naukri redirects to home page
        import re
        if re.search(r'naukri\.com/job-listings-.*-2210260\d{2}$', url):
            comp = re.sub(r'[^a-zA-Z0-9]+', '-', (self.company_name or '').lower()).strip('-')
            comp = re.sub(r'-(pvt|ltd|limited|solutions|technologies|india)$', '', comp)
            role = ''
            title_low = (self.title or '').lower()
            if 'qa' in title_low or 'test' in title_low or 'sdet' in title_low:
                role = '-qa'
            elif 'cyber' in title_low or 'security' in title_low:
                role = '-cyber-security'
            elif 'mobile' in title_low or 'flutter' in title_low or 'android' in title_low or 'ios' in title_low:
                role = '-mobile-app-developer'
            elif 'java' in title_low:
                role = '-java-developer'
            elif 'python' in title_low:
                role = '-python-developer'
            elif 'mern' in title_low or 'full stack' in title_low or 'fullstack' in title_low:
                role = '-full-stack-developer'
            elif 'frontend' in title_low or 'react' in title_low:
                role = '-frontend-developer'
            elif 'devops' in title_low or 'cloud' in title_low:
                role = '-devops-engineer'
            elif 'data' in title_low or 'analyst' in title_low:
                role = '-data-analyst'
            return f"https://www.naukri.com/{comp}{role}-jobs"

        return url

    def get_absolute_url(self):
        cat_slug = self.category.slug if self.category else 'software-tech'
        return f"/category/{cat_slug}/job/{self.uuid}/"



    def get_skills_list(self):
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def get_selection_rounds_list(self):
        """Returns a list of structured round steps from the selection_process text."""
        if not self.selection_process:
            return []
        import re
        raw_rounds = re.split(r'→|->|\n|•|(?=Round\s*\d+:?)', self.selection_process)
        cleaned = [r.strip(' -:•\t\r\n') for r in raw_rounds if r.strip(' -:•\t\r\n')]
        return cleaned if cleaned else [self.selection_process.strip()]

    def get_study_materials_list(self):
        """Returns curated study materials list or standard high-yield placement defaults."""
        if self.study_materials and isinstance(self.study_materials, list) and len(self.study_materials) > 0:
            return self.study_materials
        # Standard High-Yield Free Study Resources
        return [
            {
                "title": "Aptitude Practice Questions & Mock Tests",
                "desc": "Curated logical, quantitative, and verbal reasoning problems for the initial online screening round.",
                "url": "https://www.indiabix.com/aptitude/questions-and-answers/",
                "icon": "📖"
            },
            {
                "title": "Company-Specific Interview Preparation Corner",
                "desc": f"Detailed interview experiences, exam formats, and previous test questions for {self.company_name} and tech roles.",
                "url": "https://www.geeksforgeeks.org/company-interview-corner/",
                "icon": "🎯"
            },
            {
                "title": "Technical Placement Cheat Sheets & Question Bank",
                "desc": "High-yield coding cheat sheets, core CS fundamentals (OOP, DBMS, OS, Networks), and rapid revision guides.",
                "url": "/guides/python-interview-questions-cheat-sheet/",
                "icon": "📝"
            },
            {
                "title": "Algorithm, DSA & Live Code Debugger Practice",
                "desc": "Hands-on problem sets to improve coding speed and step-by-step memory debugging.",
                "url": "/debugger/",
                "icon": "💻"
            }
        ]

    def get_posted_date_display(self):
        """Returns human-friendly date: 'Today', 'Yesterday', or 'Aug 3, 2026' in Indian Standard Time"""
        from datetime import timedelta as td
        today = timezone.localtime(timezone.now()).date()
        yesterday = today - td(days=1)
        if self.posted_date == today:
            return 'Today'
        elif self.posted_date == yesterday:
            return 'Yesterday'
        return self.posted_date.strftime('%b %d, %Y')

    def is_last_hour(self):
        """Returns True if this job was published or discovered within the last 60 minutes."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=1)
        if self.source_published_at and self.timestamp_precision == 'EXACT_TIMESTAMP':
            return self.source_published_at >= cutoff
        return self.first_seen_at >= cutoff

    def is_within_hours(self, hours=1):
        """Returns True if published or discovered within N hours."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(hours=hours)
        if self.source_published_at and self.timestamp_precision == 'EXACT_TIMESTAMP':
            return self.source_published_at >= cutoff
        return self.first_seen_at >= cutoff

    def get_ist_published_time(self):
        """Returns publication time formatted in Asia/Kolkata timezone with precision indication."""
        from zoneinfo import ZoneInfo
        ist = ZoneInfo("Asia/Kolkata")
        target_dt = self.source_published_at or self.first_seen_at
        if not target_dt:
            return "Today"
        ist_dt = target_dt.astimezone(ist)
        if self.timestamp_precision == 'EXACT_TIMESTAMP':
            return ist_dt.strftime('%I:%M %p, %d %b')
        return ist_dt.strftime('%d %b %Y')

    def get_relative_time_display(self):
        """Returns humanized relative time (e.g., '14m ago', '2h ago', '1d ago')."""
        now = timezone.now()
        ref_time = self.source_published_at if (self.source_published_at and self.timestamp_precision == 'EXACT_TIMESTAMP') else self.first_seen_at
        if not ref_time:
            return "Recently"
        diff = now - ref_time
        total_sec = max(int(diff.total_seconds()), 0)
        if total_sec < 60:
            return "Just now"
        elif total_sec < 3600:
            return f"{total_sec // 60}m ago"
        elif total_sec < 86400:
            return f"{total_sec // 3600}h ago"
        else:
            return f"{total_sec // 86400}d ago"

    def get_experience_display(self):
        """Returns a concise, human-friendly experience requirement string."""
        import re
        if self.eligibility:
            match = re.search(r'(?:experience:?\s*)?(\d+[\s–-]+\d+\s*(?:yrs|years?))', self.eligibility, re.IGNORECASE)
            if match:
                return match.group(1).title()
            match_single = re.search(r'(\d+\+?\s*(?:yrs|years?))', self.eligibility, re.IGNORECASE)
            if match_single:
                return match_single.group(1).title()
        
        # Check description
        if self.description:
            match_desc = re.search(r'(?:experience:?\s*)?(\d+[\s–-]+\d+\s*(?:yrs|years?))', self.description, re.IGNORECASE)
            if match_desc:
                return match_desc.group(1).title()

        tier_map = {
            'INTERNSHIP': 'Internship',
            'FRESHER': 'Fresher (0-1 Yrs)',
            'EARLY_CAREER': '1-3 Years',
            'MID_LEVEL': '3-5 Years',
            'SENIOR_LEVEL': '5+ Years',
        }
        return tier_map.get(self.experience_tier, 'Fresher / All Levels')

    def get_discreet_source_code(self):
        """Returns subtle discreet code (L, N, JD, S) instead of full external brand names."""
        src = (self.source_name or '').lower()
        if 'linkedin' in src:
            return 'L'
        elif 'naukri' in src:
            return 'N'
        elif any(k in src for k in ['startup', 'ashby', 'lever', 'greenhouse']):
            return 'S'
        return 'JD'

    def get_contact_phone(self):
        """
        Extracts contact phone / mobile / WhatsApp / HR helpline number
        from description, eligibility, or selection process if present.
        """
        text = f"{self.description} {self.eligibility} {self.selection_process}"
        # 1. Standard Indian 10-digit mobile (+91 / 0 / raw 10 digits starting with 6, 7, 8, 9)
        match = re.search(r'(?:(?:\+91|91|0)[\s\-]?)?([6-9]\d{4}[\s\-]?\d{5})\b', text)
        if match:
            raw = re.sub(r'[\s\-]', '', match.group(0))
            if len(raw) == 10:
                return f"+91 {raw[:5]} {raw[5:]}"
            elif len(raw) == 12 and raw.startswith('91'):
                return f"+{raw[:2]} {raw[2:7]} {raw[7:]}"
            return match.group(0).strip()

        # 2. Toll-free helpline (1800-xxx-xxxx)
        match_toll = re.search(r'\b1800[\s\-]?\d{3}[\s\-]?\d{3,4}\b', text)
        if match_toll:
            return match_toll.group(0).strip()

        # 3. Explicit "Contact/Phone/WhatsApp/Mobile/HR: XXXXX" pattern
        match_contact = re.search(r'(?:contact|phone|mobile|whatsapp|hr\s*(?:no|num|contact)?|call)[\s\:\-]*([+]?\d[\d\s\-]{8,15}\d)', text, re.IGNORECASE)
        if match_contact:
            cleaned = match_contact.group(1).strip()
            digits = re.sub(r'\D', '', cleaned)
            if len(digits) >= 10:
                return cleaned

        return ""

    @property
    def contact_phone(self):
        return self.get_contact_phone()

    @staticmethod
    def to_unicode_bold(text):
        """Converts alphanumeric ASCII text to bold sans-serif Unicode glyphs for clean highlight in plain text."""
        out = []
        for char in str(text or ''):
            code = ord(char)
            if 65 <= code <= 90:
                out.append(chr(0x1D5D4 + (code - 65)))
            elif 97 <= code <= 122:
                out.append(chr(0x1D5EE + (code - 97)))
            elif 48 <= code <= 57:
                out.append(chr(0x1D7EC + (code - 48)))
            else:
                out.append(char)
        return "".join(out)

    def get_insta_story_text(self, include_link=False, share_url=None, base_url="https://kashiiupdatez.online"):
        """
        Generates clean, aesthetic Instagram Story text with highlighted company name,
        prominent experience requirement, salary, skills, eligibility, and optional contact.
        Apply link is excluded by default so creators can use native IG Link stickers or custom links.
        """
        url = share_url
        if not url:
            if self.category and self.uuid:
                url = f"{base_url}/category/{self.category.slug}/job/{self.uuid}/"
            elif self.uuid:
                url = f"{base_url}/job/{self.uuid}/"
            else:
                url = base_url

        exp_str = self.get_experience_display()
        is_fresher = any(k in exp_str.lower() for k in ['fresher', '0-', '0 yr', 'intern', 'entry'])
        if is_fresher:
            exp_line = f"🎯 Experience: {exp_str} 🚀 (Freshers Eligible!)"
        else:
            exp_line = f"🎯 Experience: {exp_str} ⚠️ (Experience Required)"

        skills_list = self.get_skills_list()
        if skills_list:
            skills_str = ", ".join(skills_list[:5])
        elif self.skills_required:
            skills_str = self.skills_required.strip()
        else:
            skills_str = "Software Engineering, Problem Solving"

        eligibility_str = (self.eligibility or "").strip()
        if not eligibility_str or len(eligibility_str) < 5 or 'open to eligible' in eligibility_str.lower():
            eligibility_str = "Any Graduate / BE / B.Tech / MCA / All Batches"
        elif len(eligibility_str) > 75:
            first_sent = eligibility_str.split('.')[0].strip()
            if 10 < len(first_sent) <= 75:
                eligibility_str = first_sent
            else:
                eligibility_str = "Any Graduate / BE / B.Tech / MCA / All Batches"

        company_highlight = self.to_unicode_bold((self.company_name or 'HIRING COMPANY').strip().upper())

        lines = [
            "🚨 URGENT HIRING ALERT! 🚨",
            "",
            f"🏢 Company: {company_highlight}",
            f"📌 Role: {self.title}",
            exp_line,
            f"💰 Salary / CTC: {self.stipend_salary or 'Competitive Package (Best in Industry)'}",
            f"📍 Location: {self.location or 'Pan India / Remote'}",
            f"⚡ Key Skills: {skills_str}",
            f"🎓 Eligibility: {eligibility_str}",
        ]

        if self.contact_phone:
            lines.append(f"📞 HR Contact: {self.contact_phone}")

        if include_link and url:
            lines.append(f"🔗 Apply Link: {url}")

        return "\n".join(lines)

    def get_freshness_badge(self):
        """Returns structured metadata badge for frontends and mobile cards."""
        if self.is_last_hour():
            return {
                'is_last_hour': True,
                'label': '⚡ Last 1 Hour',
                'bg': 'rgba(16, 185, 129, 0.15)',
                'border': 'rgba(16, 185, 129, 0.4)',
                'color': '#34d399',
                'title': f"Published/Discovered {self.get_relative_time_display()}"
            }
        elif self.is_within_hours(6):
            return {
                'is_last_hour': False,
                'label': '🔥 Fresh Today',
                'bg': 'rgba(56, 189, 248, 0.15)',
                'border': 'rgba(56, 189, 248, 0.35)',
                'color': '#38bdf8',
                'title': f"Published {self.get_relative_time_display()}"
            }
        return {
            'is_last_hour': False,
            'label': 'Active Drive',
            'bg': 'rgba(255, 255, 255, 0.05)',
            'border': 'rgba(255, 255, 255, 0.12)',
            'color': '#cbd5e1',
            'title': self.get_posted_date_display()
        }

    @property
    def schema_employment_type(self):
        """Standardized Schema.org employmentType for Google for Jobs."""
        mapping = {
            'INTERNSHIP': 'INTERN',
            'FULL_TIME': 'FULL_TIME',
            'PART_TIME': 'PART_TIME',
            'FREELANCE': 'CONTRACTOR',
            'CAMPUS': 'FULL_TIME',
        }
        return mapping.get(self.job_type, 'FULL_TIME')

    @property
    def schema_description_html(self):
        """Valid HTML description matching Google Search Central JobPosting guidelines."""
        import html
        parts = []
        if self.description:
            clean_desc = html.escape(self.description.strip())
            parts.append(f"<p>{clean_desc}</p>")
        if self.eligibility:
            clean_elig = html.escape(self.eligibility.strip())
            parts.append(f"<p><strong>Eligibility & Qualifications:</strong> {clean_elig}</p>")
        if self.skills_required:
            skills = [html.escape(s.strip()) for s in self.skills_required.split(',') if s.strip()]
            if skills:
                parts.append("<p><strong>Key Skills Required:</strong></p><ul>")
                for s in skills:
                    parts.append(f"<li>{s}</li>")
                parts.append("</ul>")
        if self.stipend_salary:
            parts.append(f"<p><strong>Stipend / Compensation:</strong> {html.escape(self.stipend_salary)}</p>")
        if self.location:
            parts.append(f"<p><strong>Location:</strong> {html.escape(self.location)}</p>")
        return "".join(parts) if parts else "<p>Verified student job opening on Kashii Updatez.</p>"

    def __str__(self):
        return f"{self.title} at {self.company_name} ({self.status})"

class StudentApplication(models.Model):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Under Review'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Not Selected'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    student_name = models.CharField(max_length=100)
    student_email = models.EmailField()
    student_phone = models.CharField(max_length=30, blank=True, default="")
    degree_major = models.CharField(max_length=100, default="B.Tech Computer Science")
    graduation_year = models.CharField(max_length=10, default="2026")
    resume_url = models.URLField(max_length=500, help_text="Google Drive or Cloud Resume URL")
    github_linkedin = models.URLField(max_length=500, blank=True, default="")
    cover_note = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application by {self.student_name} for {self.job.title}"

class GuideArticle(models.Model):
    TOPIC_CHOICES = [
        ('PYTHON', 'Python Programming'),
        ('DJANGO', 'Django & Web Development'),
        ('CAREER', 'Student Career & Roadmaps'),
        ('DSA', 'Data Structures & Algorithms'),
        ('INTERVIEW', 'Interview Preparation'),
        ('DEBUGGER', 'Debugging & Code Analysis'),
    ]

    STATUS_CHOICES = [
        ('PUBLISHED', 'Published'),
        ('DRAFT', 'Draft'),
    ]

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    topic = models.CharField(max_length=30, choices=TOPIC_CHOICES, default='PYTHON')
    summary = models.TextField(help_text="Concise 2-3 sentence overview for SEO meta descriptions.")
    content = models.TextField(help_text="Full rich long-form tutorial/article body.")
    read_time = models.CharField(max_length=30, default="8 min read")
    author_name = models.CharField(max_length=100, default="Kashinath (Kashii)")
    author_avatar = models.CharField(max_length=250, default="/static/images/kashii-author.jpg")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PUBLISHED')
    tags = models.CharField(max_length=250, default="Python, Career, Freshers")
    pdf_download_url = models.URLField(max_length=500, blank=True, default="", help_text="Google Drive download/view link for PDF study notes.")
    pdf_file_name = models.CharField(max_length=150, blank=True, default="", help_text="e.g. ADVANCED PYTHON BY KASHINATH.pdf")
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Guide & Tutorial"
        verbose_name_plural = "Guides & Tutorials"

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

class ContactInquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200, default="General Inquiry")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class JobGroup(models.Model):
    """Collection / Bundle of multiple job requirements for 1-click sharing & broadcasting."""
    name = models.CharField(max_length=200, help_text="e.g. 🔥 Top 5 IT Drives Today - Aug 2026")
    slug = models.SlugField(max_length=200, unique=True)
    banner_tag = models.CharField(max_length=100, default="🔥 KASHIIUPDATEZ TECH DRIVE", help_text="Header badge e.g. 🔥 KASHIIUPDATEZ TECH DRIVE")
    description = models.TextField(blank=True, default="", help_text="Optional summary of this requirement collection")
    jobs = models.ManyToManyField(JobPosting, related_name='groups', blank=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    posted_date = models.DateField(
        default=timezone.now,
        help_text="Date this drive group was posted. Defaults to today."
    )
    deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Automatically set to 7 days after creation"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Requirement Group / Bundle"
        verbose_name_plural = "Requirement Groups / Bundles"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 30-Day Auto-Expiry Policy for Hiring Drives (protects shared links against early expiry)
        if not self.deadline:
            self.deadline = timezone.now() + timedelta(days=30)
        if not self.posted_date:
            self.posted_date = timezone.localtime(timezone.now()).date()
        super().save(*args, **kwargs)
        try:
            from .backup_service import trigger_auto_backup_async
            trigger_auto_backup_async()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        try:
            from .backup_service import trigger_auto_backup_async
            trigger_auto_backup_async()
        except Exception:
            pass

    def is_expired(self):
        if not self.deadline:
            return not self.is_active
        return timezone.now() > self.deadline or not self.is_active

    def get_time_left_seconds(self):
        if not self.deadline:
            return 0
        diff = (self.deadline - timezone.now()).total_seconds()
        return max(0, int(diff))

    def get_time_left_display(self):
        sec = self.get_time_left_seconds()
        if sec <= 0:
            return "Expired"
        days = sec // 86400
        hours = (sec % 86400) // 3600
        if days > 0:
            return f"{days}d {hours}h left"
        mins = (sec % 3600) // 60
        return f"{hours}h {mins}m left"

    def get_active_jobs(self):
        return self.jobs.filter(status='ACTIVE', deadline__gt=timezone.now()).select_related('category').order_by('-created_at')



    def get_whatsapp_broadcast_text(self, host_url="https://kashiiupdatez.online"):
        lines = []
        lines.append(f"🚀 *{self.name.upper()}*")
        if self.description:
            lines.append(f"_{self.description}_\n")
        else:
            lines.append("")

        active_jobs = list(self.get_active_jobs())
        if not active_jobs:
            active_jobs = list(self.jobs.all().select_related('category')[:10])

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for idx, job in enumerate(active_jobs):
            num = number_emojis[idx] if idx < len(number_emojis) else f"{idx+1}."
            lines.append(f"{num} *{job.title}* at *{job.company_name}*")
            lines.append(f"💰 Package: {job.stipend_salary} | 📍 {job.location}")
            if job.eligibility:
                elig = (job.eligibility[:75] + '...') if len(job.eligibility) > 75 else job.eligibility
                lines.append(f"🎓 Eligibility: {elig}")
            job_link = f"{host_url}/category/{job.category.slug}/job/{job.uuid}/"
            lines.append(f"🔗 Direct Apply: {job_link}\n")

        group_url = f"{host_url}/group/{self.slug}/"
        lines.append("─────────────────────")
        lines.append(f"👉 *View all {len(active_jobs)} requirements on 1 Page:*\n{group_url}")
        lines.append("\n⚡ _Share with friends & batchmates!_")
        return "\n".join(lines)

    def get_telegram_broadcast_text(self, host_url="https://kashiiupdatez.online"):
        lines = []
        lines.append(f"🚀 **{self.name}**")
        if self.description:
            lines.append(f"{self.description}\n")
        else:
            lines.append("")

        active_jobs = list(self.get_active_jobs())
        if not active_jobs:
            active_jobs = list(self.jobs.all().select_related('category')[:10])

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for idx, job in enumerate(active_jobs):
            num = number_emojis[idx] if idx < len(number_emojis) else f"{idx+1}."
            lines.append(f"{num} **{job.title}** — __{job.company_name}__")
            lines.append(f"• 💰 Package: `{job.stipend_salary}` | 📍 `{job.location}`")
            job_link = f"{host_url}/category/{job.category.slug}/job/{job.uuid}/"
            lines.append(f"• 🔗 [Direct Application Link]({job_link})\n")

        group_url = f"{host_url}/group/{self.slug}/"
        lines.append(f"👉 **[Click Here to Open Full {len(active_jobs)}-Job Group Page]({group_url})**")
        return "\n".join(lines)


class SiteVisit(models.Model):
    """
    Lightweight, high-performance visitor analytics tracking.
    Enables free-tier owners to monitor total users, unique visitors,
    page views, referrer traffic (Instagram, Google, Direct, WhatsApp),
    and device statistics without third-party subscriptions.
    """
    visitor_hash = models.CharField(max_length=64, db_index=True, help_text="SHA-256 hash of IP + User-Agent for unique visitor counting")
    path = models.CharField(max_length=500, db_index=True)
    page_title = models.CharField(max_length=255, blank=True, default="")
    referrer = models.CharField(max_length=100, default="Direct", db_index=True)
    referrer_raw = models.CharField(max_length=500, blank=True, default="")
    device_type = models.CharField(max_length=20, default="Desktop", db_index=True)
    browser = models.CharField(max_length=50, default="Other")
    os = models.CharField(max_length=50, default="Other")
    user_agent = models.CharField(max_length=500, blank=True, default="")
    ip_address_masked = models.CharField(max_length=45, blank=True, default="")
    is_bot = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['is_bot', 'timestamp']),
            models.Index(fields=['timestamp', 'is_bot']),
            models.Index(fields=['visitor_hash', 'timestamp']),
            models.Index(fields=['path', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.device_type} visit to {self.path} at {self.timestamp}"


class ResumeGenerationJob(models.Model):
    """
    Persistent background job tracker for Job-Specific AI Resume Generation
    and GitHub Project Discovery. Supports mobile-first async polling.
    """
    MODE_CHOICES = [
        ('FRESHER_GITHUB', 'Fresher with GitHub Discovery'),
        ('EXISTING_UPLOAD', 'Existing Resume Tailoring'),
        ('SCRATCH', 'Start from Scratch'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Initialization'),
        ('EXTRACTING_SKILLS', 'Extracting Skills & Requirements'),
        ('SEARCHING_REPOSITORIES', 'Searching Public GitHub Repositories'),
        ('RANKING_PROJECTS', 'Ranking Discovered Projects'),
        ('AWAITING_SELECTION', 'Awaiting Candidate Selection'),
        ('GENERATING_RESUME', 'Generating Tailored Resume'),
        ('EVALUATING_ATS', 'Evaluating ATS Score & Metrics'),
        ('COMPLETED', 'Completed Successfully'),
        ('FAILED', 'Failed with Error'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    session_key = models.CharField(max_length=64, blank=True, default='', db_index=True)
    job = models.ForeignKey(JobPosting, on_delete=models.SET_NULL, null=True, blank=True, related_name='resume_generations')
    mode = models.CharField(max_length=30, choices=MODE_CHOICES, default='FRESHER_GITHUB')
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    progress_pct = models.PositiveSmallIntegerField(default=0)
    stage_message = models.CharField(max_length=255, default='Job initialized...')
    
    candidate_data = models.JSONField(default=dict, blank=True)
    # Target role for resumes built on the standalone studio page, where there is
    # no JobPosting to point at. Keys: title, company, skills, description, location.
    target_profile = models.JSONField(default=dict, blank=True)
    generated_resume = models.JSONField(default=dict, blank=True)
    ats_evaluation = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['session_key', '-created_at']),
        ]

    def __str__(self):
        return f"ResumeGenJob {self.uuid} ({self.mode} - {self.status} {self.progress_pct}%)"


class IndianDemoProject(models.Model):
    """
    Curated library of realistic, fictional demonstration and portfolio projects
    based on Indian IT industry use cases across major technology hubs.
    Explicitly labeled as fictional practice/portfolio projects.
    """
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    title = models.CharField(max_length=250)
    fictional_company_name = models.CharField(max_length=200, blank=True, default='')
    location_city = models.CharField(max_length=100, db_index=True)
    location_state = models.CharField(max_length=100, db_index=True)
    industry = models.CharField(max_length=100, db_index=True)
    
    target_job_roles = models.JSONField(default=list, help_text="e.g. ['Python / Django', 'Backend Engineer']")
    difficulty_level = models.CharField(max_length=30, choices=DIFFICULTY_CHOICES, default='Intermediate', db_index=True)
    project_type = models.CharField(max_length=80, default='Personal Portfolio Project')
    
    description = models.TextField()
    problem_statement = models.TextField(blank=True, default='')
    technical_stack = models.JSONField(default=list, help_text="List of technologies, frameworks, and databases")
    key_features = models.JSONField(default=list)
    
    architecture_summary = models.TextField(blank=True, default='')
    database_design_summary = models.TextField(blank=True, default='')
    api_design_summary = models.TextField(blank=True, default='')
    
    resume_bullet_templates = models.JSONField(default=list, help_text="3-5 Google XYZ bullet templates")
    estimated_duration = models.CharField(max_length=50, default='3-4 weeks')
    learning_outcomes = models.JSONField(default=list, blank=True)
    
    source_type = models.CharField(max_length=50, default='CURATED_INDIAN_DEMO')
    is_curated = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['location_city', 'title']
        indexes = [
            models.Index(fields=['location_city', 'is_active']),
            models.Index(fields=['industry', 'is_active']),
            models.Index(fields=['difficulty_level', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} — {self.location_city} ({self.difficulty_level})"


class DiscoveredProject(models.Model):
    """
    Discovered GitHub public repositories ranked for relevance to target job skills.
    Maintains ethical boundaries: candidate can select whether they Built, Contributed,
    or are using it as a Recommended study project.
    """
    RELATIONSHIP_CHOICES = [
        ('BUILT', 'Built / Authored Personally'),
        ('PORTFOLIO', 'Personal Portfolio Project (Demonstration)'),
        ('PRACTICE', 'Guided Practice / Case Study'),
        ('CONTRIBUTED', 'Contributed / Forked / Enhanced'),
        ('RECOMMENDED', 'Architecture Case Study'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    generation_job = models.ForeignKey(ResumeGenerationJob, on_delete=models.CASCADE, related_name='discovered_projects')
    demo_project = models.ForeignKey(IndianDemoProject, on_delete=models.SET_NULL, null=True, blank=True, related_name='discovered_instances')
    repo_name = models.CharField(max_length=200)
    repo_url = models.URLField(max_length=500)
    description = models.TextField(blank=True, default='')
    stars = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=100, blank=True, default='')
    tech_stack = models.JSONField(default=list, blank=True)
    
    relevance_score = models.FloatField(default=0.0, help_text="0-100 score based on 5-factor relevance formula")
    score_breakdown = models.JSONField(default=dict, blank=True)
    evidence_summary = models.TextField(blank=True, default='')
    
    candidate_relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES, default='RECOMMENDED')
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-relevance_score', '-stars']
        indexes = [
            models.Index(fields=['generation_job', '-relevance_score']),
            models.Index(fields=['generation_job', 'is_selected']),
        ]

    def __str__(self):
        return f"{self.repo_name} (Score: {self.relevance_score:.1f}) for Job {self.generation_job.uuid}"


class JobIngestionRun(models.Model):
    """
    Tracks periodic ingestion metrics, per-source execution history,
    failure isolation, and health diagnostics for India-wide job scraping.
    """
    STATUS_CHOICES = [
        ('RUNNING', 'Running Ingestion'),
        ('SUCCESS', 'Success'),
        ('PARTIAL', 'Partial with Warnings'),
        ('FAILED', 'Failed with Errors'),
    ]

    batch_id = models.CharField(max_length=64, unique=True, db_index=True)
    source_name = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    jobs_discovered = models.PositiveIntegerField(default=0)
    jobs_imported = models.PositiveIntegerField(default=0)
    duplicates_skipped = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source_name', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]

    def __str__(self):
        return f"{self.source_name} ({self.status}) - {self.jobs_imported} imported at {self.started_at}"





