import uuid
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
    skills_required = models.CharField(max_length=300, help_text="Comma-separated skills e.g. Python, React, SQL")
    
    apply_url = models.URLField(max_length=500, blank=True, null=True, help_text="Official external application link")
    allow_direct_apply = models.BooleanField(default=True)

    description = models.TextField(help_text="Detailed job description and responsibilities")
    eligibility = models.TextField(blank=True, default="Open to all students")
    
    posted_by = models.CharField(max_length=100, default="Kashii Updatez Admin")
    poster_email = models.EmailField(default="admin@kashiiupdatez.com")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    # 7-Day Auto Expiration Policy
    created_at = models.DateTimeField(auto_now_add=True)
    posted_date = models.DateField(
        default=timezone.now,
        help_text="Date this requirement was posted (editable). Defaults to today."
    )
    deadline = models.DateTimeField(help_text="Automatically set to 7 days after posting")
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-set 7-day deadline upon creation if not explicitly set
        if not self.deadline:
            self.deadline = timezone.now() + timedelta(days=7)
        # Auto-set posted_date from today if not set
        if not self.posted_date:
            self.posted_date = timezone.now().date()
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.deadline

    def get_skills_list(self):
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def get_posted_date_display(self):
        """Returns human-friendly date: 'Today', 'Yesterday', or 'Aug 3, 2026'"""
        from datetime import timedelta as td
        today = timezone.now().date()
        yesterday = today - td(days=1)
        if self.posted_date == today:
            return 'Today'
        elif self.posted_date == yesterday:
            return 'Yesterday'
        return self.posted_date.strftime('%b %d, %Y')

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
    banner_tag = models.CharField(max_length=100, default="🔥 DAILY MEGA HIRING DRIVE", help_text="Header badge e.g. 💼 DELOITTE SPECIAL")
    description = models.TextField(blank=True, default="", help_text="Optional summary of this requirement collection")
    jobs = models.ManyToManyField(JobPosting, related_name='groups', blank=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Requirement Group / Bundle"
        verbose_name_plural = "Requirement Groups / Bundles"

    def __str__(self):
        return self.name

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


