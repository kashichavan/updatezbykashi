import logging
from django.utils import timezone
from ..models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)
from .instagram_api import InstagramAPI

logger = logging.getLogger(__name__)

class AutomationEngine:
    """
    Core Automation Engine for processing incoming Instagram Webhooks
    (Comments & Messages) and executing Comment -> DM -> Follow/DONE workflows.
    """

    def process_comment_event(self, account, event_data):
        """
        Handles incoming comment webhook payload from Meta/Instagram.
        Payload format sample:
        {
            'id': '179...', # comment_id
            'text': 'python guide',
            'from': {'id': '12345', 'username': 'johndoe'},
            'media': {'id': '67890'}
        }
        """
        comment_id = event_data.get('id') or event_data.get('comment_id')
        comment_text = (event_data.get('text') or '').strip()
        sender_info = event_data.get('from', {})
        participant_id = sender_info.get('id')
        participant_username = sender_info.get('username', '')

        if not comment_id or not comment_text or not participant_id:
            return {'status': 'SKIPPED', 'reason': 'Missing required comment fields'}

        # Deduplication check
        exec_id = f"comment_{comment_id}"
        if AutomationExecution.objects.filter(external_event_id=exec_id).exists():
            return {'status': 'SKIPPED', 'reason': 'Duplicate event'}

        # Find matching active automation
        automations = CommentAutomation.objects.filter(
            instagram_account=account,
            is_active=True
        )

        media_id = event_data.get('media', {}).get('id') or event_data.get('media_id')

        matched_automation = None
        for auto in automations:
            # Check target scope (Specific Reel vs All Reels)
            if auto.target_scope == CommentAutomation.TargetScope.SPECIFIC_REEL and auto.specific_reel_id:
                clean_target_id = auto.specific_reel_id.strip()
                if media_id and clean_target_id not in media_id and media_id not in clean_target_id:
                    continue

            keywords = auto.get_keywords_list()
            comment_lower = comment_text.lower()
            if any(kw in comment_lower for kw in keywords):
                matched_automation = auto
                break

        if not matched_automation:
            return {'status': 'SKIPPED', 'reason': 'No keyword or Reel target match'}

        api = InstagramAPI(account)

        # 1. Reply publicly to comment if specified
        if matched_automation.comment_reply:
            try:
                api.reply_to_comment(comment_id, matched_automation.comment_reply)
            except Exception as e:
                logger.error(f"Failed to post public comment reply: {e}")

        # 2. Send DM / Private Reply with Follower Check Notice
        dm_text = matched_automation.dm_message.replace('{{username}}', participant_username or 'there').replace('{{account_username}}', account.username)

        try:
            res = api.send_private_reply(comment_id, dm_text)
            if not res or 'error' in res:
                # Fallback to direct message
                res = api.send_direct_message(participant_id, dm_text)
        except Exception as e:
            logger.error(f"Error sending DM for comment: {e}")

        # 3. Create or Update Conversation State
        conv, _ = InstagramConversation.objects.get_or_create(
            instagram_account=account,
            participant_id=participant_id,
            defaults={'participant_username': participant_username}
        )
        if participant_username and conv.participant_username != participant_username:
            conv.participant_username = participant_username

        conv.active_automation = matched_automation
        conv.awaiting_confirmation = True
        conv.save()

        # Record outgoing DM message
        InstagramMessage.objects.create(
            conversation=conv,
            sender_id=account.instagram_user_id,
            message_text=dm_text,
            direction=InstagramMessage.Direction.OUTGOING
        )

        # Record Execution
        execution = AutomationExecution.objects.create(
            automation=matched_automation,
            external_event_id=exec_id,
            event_type=AutomationExecution.EventType.COMMENT,
            status=AutomationExecution.Status.SUCCESS
        )

        return {'status': 'SUCCESS', 'execution_id': execution.id, 'automation': matched_automation.name}

    def process_message_event(self, account, event_data):
        """
        Handles incoming direct message webhook payload.
        Payload format sample:
        {
            'mid': 'm_123...',
            'sender': {'id': '12345'},
            'message': {'text': 'DONE'}
        }
        """
        message_id = event_data.get('mid') or event_data.get('message_id')
        sender_id = event_data.get('sender', {}).get('id') or event_data.get('sender_id')
        message_text = (event_data.get('message', {}).get('text') or event_data.get('text') or '').strip()

        if not sender_id or not message_text or sender_id == account.instagram_user_id:
            return {'status': 'SKIPPED', 'reason': 'Invalid or self-sent message'}

        exec_id = f"msg_{message_id}" if message_id else f"msg_{sender_id}_{timezone.now().timestamp()}"
        if message_id and AutomationExecution.objects.filter(external_event_id=exec_id).exists():
            return {'status': 'SKIPPED', 'reason': 'Duplicate message event'}

        conv, _ = InstagramConversation.objects.get_or_create(
            instagram_account=account,
            participant_id=sender_id
        )

        # Record incoming message
        InstagramMessage.objects.create(
            conversation=conv,
            message_id=message_id or '',
            sender_id=sender_id,
            message_text=message_text,
            direction=InstagramMessage.Direction.INCOMING
        )

        api = InstagramAPI(account)
        matched_automation = None
        reply_text = ""

        # Check if conversation is awaiting DONE confirmation keyword
        if conv.awaiting_confirmation and conv.active_automation:
            auto = conv.active_automation
            if message_text.lower() == auto.confirmation_keyword.lower():
                matched_automation = auto
                reply_text = auto.final_message.replace('{{resource_url}}', auto.resource_url).replace('{{username}}', conv.participant_username or 'there')
                conv.awaiting_confirmation = False
                conv.active_automation = None
                conv.save()

        # If not confirmation keyword match, check direct message automations
        if not matched_automation:
            automations = CommentAutomation.objects.filter(
                instagram_account=account,
                is_active=True
            )
            for auto in automations:
                keywords = auto.get_keywords_list()
                if any(kw in message_text.lower() for kw in keywords):
                    matched_automation = auto
                    reply_text = auto.final_message.replace('{{resource_url}}', auto.resource_url).replace('{{username}}', conv.participant_username or 'there')
                    break

        if matched_automation and reply_text:
            api.send_direct_message(sender_id, reply_text)
            
            InstagramMessage.objects.create(
                conversation=conv,
                sender_id=account.instagram_user_id,
                message_text=reply_text,
                direction=InstagramMessage.Direction.OUTGOING
            )

            execution = AutomationExecution.objects.create(
                automation=matched_automation,
                external_event_id=exec_id,
                event_type=AutomationExecution.EventType.CONFIRMATION if conv.awaiting_confirmation else AutomationExecution.EventType.MESSAGE,
                status=AutomationExecution.Status.SUCCESS
            )
            return {'status': 'SUCCESS', 'execution_id': execution.id}

        return {'status': 'SKIPPED', 'reason': 'No matching message keyword'}
