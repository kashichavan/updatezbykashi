from django.db import models
import uuid

class InstagramAccount(models.Model):
    account_id = models.CharField(max_length=100, unique=True, help_text="Meta Page / Instagram User ID")
    username = models.CharField(max_length=150, help_text="Instagram Account Handle (e.g. @pythonkashi)")
    page_access_token = models.TextField(help_text="Meta Page Long-Lived User Access Token")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.username} ({self.account_id})"

class AutomationRule(models.Model):
    TARGET_SCOPE_CHOICES = (
        ('ALL_REELS', 'All Reels & Posts'),
        ('SPECIFIC_REEL', 'Specific Reel / Post'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name='rules', null=True, blank=True)
    name = models.CharField(max_length=200, help_text="Rule Title (e.g. Python Job Link DM)")
    target_scope = models.CharField(max_length=20, choices=TARGET_SCOPE_CHOICES, default='ALL_REELS')
    reel_url_or_id = models.CharField(max_length=300, blank=True, null=True, help_text="Target Instagram Reel URL or Media ID (if SPECIFIC_REEL)")
    trigger_keyword = models.CharField(max_length=100, help_text="Comment keyword to trigger automation (e.g. python, link, job)")
    comment_reply_text = models.TextField(help_text="Public comment reply template (use {username} for dynamic tag)")
    private_dm_text = models.TextField(help_text="Private DM message body")
    resource_url = models.URLField(blank=True, null=True, help_text="Resource link included in DM / follow gate")
    enforce_follower_gate = models.BooleanField(default=True, help_text="Require user to follow account before delivering link")
    follower_gate_message = models.TextField(default="Thanks for your comment! 👋 Please follow @{account_username} and reply 'DONE' to get your instant direct access link!", help_text="Message sent if user is not following")
    is_active = models.BooleanField(default=True)
    trigger_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [Trigger: '{self.trigger_keyword}']"

class AutomationLog(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success - DM Delivered'),
        ('GATE_SENT', 'Follower Gate Sent'),
        ('FAILED', 'Execution Failed'),
        ('IGNORED', 'Keyword Not Matched'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    rule = models.ForeignKey(AutomationRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    comment_id = models.CharField(max_length=150)
    commenter_username = models.CharField(max_length=150)
    commenter_id = models.CharField(max_length=150, blank=True, null=True)
    media_id = models.CharField(max_length=150, blank=True, null=True)
    comment_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS')
    response_details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Log: @{self.commenter_username} - {self.status} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
