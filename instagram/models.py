import uuid
from django.db import models
from django.conf import settings

class InstagramAccount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    instagram_user_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    profile_picture = models.URLField(blank=True, null=True)
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"@{self.username} ({self.instagram_user_id})"

class Automation(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('DRAFT', 'Draft'),
    )
    TRIGGER_CHOICES = (
        ('ANY_COMMENT', 'Any Comment'),
        ('KEYWORD', 'Keyword'),
    )
    instagram_account = models.ForeignKey(InstagramAccount, on_delete=models.CASCADE, related_name='automations')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    reel_id = models.CharField(max_length=255, blank=True, null=True, help_text="Specific Reel ID or leave empty for all reels")
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_CHOICES, default='KEYWORD')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.status}]"

class AutomationTrigger(models.Model):
    MATCH_CHOICES = (
        ('CONTAINS', 'Contains Keyword'),
        ('EXACT', 'Exact Match'),
    )
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='triggers')
    keyword = models.CharField(max_length=255)
    match_type = models.CharField(max_length=50, choices=MATCH_CHOICES, default='CONTAINS')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Trigger '{self.keyword}' ({self.match_type})"

class AutomationAction(models.Model):
    ACTION_CHOICES = (
        ('REPLY_COMMENT', 'Reply to Comment'),
        ('SEND_DM', 'Send Direct Message'),
    )
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    configuration = models.JSONField(default=dict, help_text="Stores messages, reply variations, links, variables")
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Action {self.action_type} (Order {self.order})"

class CommentEvent(models.Model):
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, null=True, blank=True, related_name='comment_events')
    instagram_comment_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    comment_text = models.TextField()
    processed = models.BooleanField(default=False)
    matched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment @{self.username}: {self.comment_text[:30]}"

class AutomationExecution(models.Model):
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    )
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='executions')
    comment_event = models.ForeignKey(CommentEvent, on_delete=models.CASCADE, related_name='executions')
    action = models.ForeignKey(AutomationAction, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    response = models.JSONField(default=dict, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-executed_at']

    def __str__(self):
        return f"Execution {self.status} for @{self.comment_event.username}"
