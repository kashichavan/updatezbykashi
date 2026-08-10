# Task stubs / Celery helpers for async processing if Celery is enabled
import logging
from .services.automation import AutomationEngine
from .models import InstagramAccount

logger = logging.getLogger(__name__)

def process_comment_async(account_id, event_data):
    account = InstagramAccount.objects.filter(id=account_id).first()
    if account:
        engine = AutomationEngine()
        return engine.process_comment_event(account, event_data)

def process_message_async(account_id, event_data):
    account = InstagramAccount.objects.filter(id=account_id).first()
    if account:
        engine = AutomationEngine()
        return engine.process_message_event(account, event_data)
