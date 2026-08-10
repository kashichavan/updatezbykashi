import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class InstagramAccount(models.Model):
    class ConnectionStatus(models.TextChoices):
        CONNECTED = 'CONNECTED', 'Connected'
        DISCONNECTED = 'DISCONNECTED', 'Disconnected'
        TOKEN_EXPIRED = 'TOKEN_EXPIRED', 'Token Expired'
        REAUTH_REQUIRED = 'REAUTH_REQUIRED', 'Reauth Required'
        ERROR = 'ERROR', 'Error'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='instagram_accounts'
    )
    instagram_user_id = models.CharField(max_length=128, unique=True, db_index=True)
    username = models.CharField(max_length=128, db_index=True)
    display_name = models.CharField(max_length=255, blank=True, default='')
    profile_picture = models.URLField(max_length=1024, blank=True, default='')
    account_type = models.CharField(max_length=64, blank=True, default='BUSINESS')
    
    access_token = models.TextField(blank=True, default='')
    token_expires_at = models.DateTimeField(null=True, blank=True)
    scopes = models.CharField(max_length=512, blank=True, default='')
    
    is_active = models.BooleanField(default=True)
    is_connected = models.BooleanField(default=True)
    connection_status = models.CharField(
        max_length=32,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.CONNECTED
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    connection_error = models.TextField(blank=True, default='')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Instagram Account'
        verbose_name_plural = 'Instagram Accounts'

    def __str__(self):
        return f"@{self.username} ({self.get_connection_status_display()})"

    @property
    def is_token_valid(self):
        if not self.access_token:
            return False
        if self.token_expires_at and self.token_expires_at <= timezone.now():
            return False
        return self.is_connected and self.connection_status == self.ConnectionStatus.CONNECTED


class CommentAutomation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='comment_automations'
    )
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='automations'
    )
    name = models.CharField(max_length=255, help_text="Short descriptive name for this rule (e.g. Python Guide)")
    keywords = models.TextField(help_text="Comma-separated trigger keywords (e.g. python, python guide)")
    comment_reply = models.TextField(blank=True, default="Thanks! 👋 Check your DM.", help_text="Public comment reply text")
    dm_message = models.TextField(blank=True, default="Hey {{username}} 👋 Follow us and reply DONE to receive the resource.", help_text="Initial DM message text")
    confirmation_keyword = models.CharField(max_length=64, default="DONE", help_text="Keyword user sends to get final resource")
    final_message = models.TextField(blank=True, default="Awesome! 🎉 Here is your guide: {{resource_url}}", help_text="Final DM text containing resource link")
    resource_url = models.URLField(max_length=1024, blank=True, default="", help_text="URL of resource/guide to send")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comment & DM Automation'
        verbose_name_plural = 'Comment & DM Automations'

    def __str__(self):
        return f"{self.name} (@{self.instagram_account.username})"

    def get_keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


class InstagramConversation(models.Model):
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    participant_id = models.CharField(max_length=128, db_index=True)
    participant_username = models.CharField(max_length=128, blank=True, default='')
    last_message_at = models.DateTimeField(auto_now=True)
    active_automation = models.ForeignKey(
        CommentAutomation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='active_conversations'
    )
    awaiting_confirmation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']
        unique_together = ['instagram_account', 'participant_id']
        verbose_name = 'Instagram Conversation'
        verbose_name_plural = 'Instagram Conversations'

    def __str__(self):
        name = f"@{self.participant_username}" if self.participant_username else self.participant_id
        return f"Chat with {name} on @{self.instagram_account.username}"


class InstagramMessage(models.Model):
    class Direction(models.TextChoices):
        INCOMING = 'INCOMING', 'Incoming'
        OUTGOING = 'OUTGOING', 'Outgoing'

    conversation = models.ForeignKey(
        InstagramConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    message_id = models.CharField(max_length=255, blank=True, default='', db_index=True)
    sender_id = models.CharField(max_length=128)
    message_text = models.TextField()
    direction = models.CharField(max_length=16, choices=Direction.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Instagram Message'
        verbose_name_plural = 'Instagram Messages'

    def __str__(self):
        return f"[{self.direction}] {self.message_text[:30]}"


class AutomationExecution(models.Model):
    class EventType(models.TextChoices):
        COMMENT = 'COMMENT', 'Comment Event'
        MESSAGE = 'MESSAGE', 'Message Event'
        CONFIRMATION = 'CONFIRMATION', 'Confirmation Keyword Event'

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        SKIPPED = 'SKIPPED', 'Skipped'

    automation = models.ForeignKey(
        CommentAutomation,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    external_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUCCESS)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Automation Execution'
        verbose_name_plural = 'Automation Executions'

    def __str__(self):
        return f"{self.automation.name} - {self.event_type} - {self.status}"
