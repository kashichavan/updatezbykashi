from rest_framework import serializers
from .models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)

class InstagramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramAccount
        fields = [
            'id', 'instagram_user_id', 'username', 'display_name',
            'profile_picture', 'account_type', 'is_active', 'is_connected',
            'connection_status', 'last_synced_at', 'connection_error',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CommentAutomationSerializer(serializers.ModelSerializer):
    keywords_list = serializers.ListField(child=serializers.CharField(), read_only=True, source='get_keywords_list')
    instagram_username = serializers.CharField(source='instagram_account.username', read_only=True)

    class Meta:
        model = CommentAutomation
        fields = [
            'id', 'instagram_account', 'instagram_username', 'name',
            'keywords', 'keywords_list', 'comment_reply', 'dm_message',
            'confirmation_keyword', 'final_message', 'resource_url',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class InstagramMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramMessage
        fields = ['id', 'conversation', 'message_id', 'sender_id', 'message_text', 'direction', 'created_at']
        read_only_fields = ['id', 'created_at']

class InstagramConversationSerializer(serializers.ModelSerializer):
    messages = InstagramMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = InstagramConversation
        fields = [
            'id', 'instagram_account', 'participant_id', 'participant_username',
            'last_message_at', 'awaiting_confirmation', 'messages', 'created_at'
        ]
        read_only_fields = ['id', 'last_message_at', 'created_at']

class AutomationExecutionSerializer(serializers.ModelSerializer):
    automation_name = serializers.CharField(source='automation.name', read_only=True)

    class Meta:
        model = AutomationExecution
        fields = [
            'id', 'automation', 'automation_name', 'external_event_id',
            'event_type', 'status', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
