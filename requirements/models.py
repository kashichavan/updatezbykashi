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
        ('EXPIRED', 'Deactivated / Expired (3-Day Auto-Closed)'),
        ('CLOSED', 'Manually Closed'),
    ]

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
    
    # 3-Day Auto Expiration Policy
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(help_text="Automatically set to 3 days after posting")
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-set 3-day deadline upon creation if not explicitly set
        if not self.deadline:
            self.deadline = timezone.now() + timedelta(days=3)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.deadline

    def get_skills_list(self):
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

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
