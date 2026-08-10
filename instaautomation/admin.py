from django.contrib import admin
from .models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)

@admin.register(InstagramAccount)
class InstagramAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'instagram_user_id', 'connection_status', 'is_connected', 'is_active', 'token_expires_at', 'created_at')
    list_filter = ('connection_status', 'is_connected', 'is_active', 'created_at')
    search_fields = ('username', 'display_name', 'instagram_user_id')
    readonly_fields = ('access_token', 'created_at', 'updated_at')

@admin.register(CommentAutomation)
class CommentAutomationAdmin(admin.ModelAdmin):
    list_display = ('name', 'instagram_account', 'keywords', 'confirmation_keyword', 'is_active', 'created_at')
    list_filter = ('is_active', 'instagram_account', 'created_at')
    search_fields = ('name', 'keywords', 'comment_reply', 'dm_message')

@admin.register(InstagramConversation)
class InstagramConversationAdmin(admin.ModelAdmin):
    list_display = ('participant_username', 'participant_id', 'instagram_account', 'awaiting_confirmation', 'last_message_at')
    list_filter = ('awaiting_confirmation', 'instagram_account', 'last_message_at')
    search_fields = ('participant_username', 'participant_id')

@admin.register(InstagramMessage)
class InstagramMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'direction', 'sender_id', 'short_message', 'created_at')
    list_filter = ('direction', 'created_at')
    search_fields = ('message_text', 'sender_id')

    def short_message(self, obj):
        return obj.message_text[:50]
    short_message.short_description = "Message Text"

@admin.register(AutomationExecution)
class AutomationExecutionAdmin(admin.ModelAdmin):
    list_display = ('automation', 'event_type', 'status', 'external_event_id', 'created_at')
    list_filter = ('status', 'event_type', 'created_at')
    search_fields = ('external_event_id', 'error_message')
