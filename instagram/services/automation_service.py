import json
import logging
from django.db import transaction
from ..models import Automation, CommentEvent, AutomationExecution, AutomationTrigger, AutomationAction
from .instagram_client import InstagramClient
from .comment_service import CommentService
from .messaging_service import MessagingService

logger = logging.getLogger(__name__)

class AutomationService:
    @staticmethod
    def process_comment_event(comment_id, username, comment_text, media_id=None, commenter_id=None):
        """
        Processes an incoming comment event with strict IDEMPOTENCY.
        """
        # IDEMPOTENCY CHECK: Return early if comment already recorded
        if CommentEvent.objects.filter(instagram_comment_id=comment_id).exists():
            logger.info(f"Idempotency Guard: Event {comment_id} already processed. Skipping.")
            return {'status': 'DUPLICATE_SKIPPED'}

        active_automations = Automation.objects.filter(status='ACTIVE')
        matched_automation = None
        matched_trigger = None

        for auto in active_automations:
            # Check Reel ID filter if configured
            if auto.reel_id and media_id and auto.reel_id not in media_id and media_id not in auto.reel_id:
                continue

            if auto.trigger_type == 'ANY_COMMENT':
                matched_automation = auto
                break
            elif auto.trigger_type == 'KEYWORD':
                triggers = auto.triggers.filter(is_active=True)
                for tr in triggers:
                    kw = tr.keyword.strip().lower()
                    text = comment_text.strip().lower()

                    if tr.match_type == 'EXACT':
                        if text == kw:
                            matched_automation = auto
                            matched_trigger = tr
                            break
                    else: # CONTAINS
                        if kw in text:
                            matched_automation = auto
                            matched_trigger = tr
                            break
                if matched_automation:
                    break

        # Record Comment Event atomically
        with transaction.atomic():
            comment_event = CommentEvent.objects.create(
                automation=matched_automation,
                instagram_comment_id=comment_id,
                username=username,
                comment_text=comment_text,
                processed=True,
                matched=bool(matched_automation)
            )

        if not matched_automation:
            logger.info(f"No active automation matched comment: '{comment_text}' by @{username}")
            return {'status': 'NO_MATCH'}

        # Execute Actions sequentially
        client = InstagramClient(access_token=matched_automation.instagram_account.access_token if matched_automation.instagram_account else None)
        actions = matched_automation.actions.filter(is_active=True).order_by('order')

        results = []
        for action in actions:
            config = action.configuration or {}

            if action.action_type == 'REPLY_COMMENT':
                reply_text = config.get('reply_text') or CommentService.select_reply_variation(config.get('reply_variations', []), username)
                res = client.reply_to_comment(comment_id, reply_text)
                status = 'SUCCESS' if res.get('success') else 'FAILED'

                AutomationExecution.objects.create(
                    automation=matched_automation,
                    comment_event=comment_event,
                    action=action,
                    status=status,
                    response=res.get('data'),
                    error_message=str(res.get('error')) if not res.get('success') else None
                )
                results.append(status)

            elif action.action_type == 'SEND_DM':
                recipient = commenter_id or username
                dm_template = config.get('dm_text', 'Hey {{username}}, here is your requested link: {{link}}')
                link = config.get('resource_url', '')

                formatted_dm = MessagingService.format_dm_message(
                    dm_template,
                    username=username,
                    comment=comment_text,
                    link=link
                )

                res = client.send_message(recipient, formatted_dm)
                status = 'SUCCESS' if res.get('success') else 'FAILED'

                AutomationExecution.objects.create(
                    automation=matched_automation,
                    comment_event=comment_event,
                    action=action,
                    status=status,
                    response=res.get('data'),
                    error_message=str(res.get('error')) if not res.get('success') else None
                )
                results.append(status)

        return {'status': 'EXECUTED', 'results': results}
