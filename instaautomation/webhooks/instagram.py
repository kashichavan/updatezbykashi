import json
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import InstagramAccount
from ..services.automation import AutomationEngine

logger = logging.getLogger(__name__)

@csrf_exempt
def instagram_webhook(request):
    """
    Official Meta / Instagram Webhook endpoint.
    GET: Handles Meta Webhook Verification (hub.challenge)
    POST: Processes real-time comment and message events from Meta Graph API
    """
    if request.method == 'GET':
        verify_token = str(getattr(settings, 'META_VERIFY_TOKEN', '') or '8722183087')
        hub_mode = request.GET.get('hub.mode')
        hub_token = request.GET.get('hub.verify_token')
        hub_challenge = request.GET.get('hub.challenge')

        accepted_tokens = {verify_token, '8722183087', 'kashii_insta_verify_token_2026'}

        if hub_mode == 'subscribe' and hub_token in accepted_tokens:
            logger.info(f"Meta Webhook successfully verified with token: {hub_token}")
            return HttpResponse(hub_challenge, content_type='text/plain', status=200)
        else:
            logger.warning(f"Meta Webhook verification failed. Received token: {hub_token}, Expected one of: {accepted_tokens}")
            return HttpResponse("Verification failed", status=403)

    elif request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            return JsonResponse({'status': 'invalid json', 'error': str(e)}, status=400)

        # Process entries
        entries = payload.get('entry', [])
        engine = AutomationEngine()

        for entry in entries:
            account_id = entry.get('id')
            account = InstagramAccount.objects.filter(
                instagram_user_id=account_id,
                is_connected=True,
                is_active=True
            ).first()

            if not account:
                # Attempt lookup by username or first active connected account if system has single test account
                account = InstagramAccount.objects.filter(is_connected=True, is_active=True).first()

            if not account:
                continue

            # Check comments changes
            changes = entry.get('changes', [])
            for change in changes:
                field = change.get('field')
                value = change.get('value', {})
                if field == 'comments':
                    engine.process_comment_event(account, value)

            # Check direct messages
            messaging = entry.get('messaging', [])
            for msg in messaging:
                engine.process_message_event(account, msg)

        return JsonResponse({'status': 'EVENT_RECEIVED'}, status=200)

    return HttpResponse("Method not allowed", status=405)
