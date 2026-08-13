import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import InstagramAccount, Automation, AutomationTrigger, AutomationAction, CommentEvent, AutomationExecution
from .services.automation_service import AutomationService
from requirements.views import is_authenticated_owner

logger = logging.getLogger(__name__)

META_VERIFY_TOKEN = '8722183087'

# --- 1. WEBHOOK HANDLER (IDEMPOTENT & ASYNC-READY) ---

@csrf_exempt
def webhook_endpoint(request):
    """Official Meta Webhook Verification (GET) and Comment Listener (POST)."""
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == META_VERIFY_TOKEN:
            logger.info("Meta Webhook Verification Succeeded!")
            return HttpResponse(challenge, status=200)
        return HttpResponse("Verification failed", status=403)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            entries = body.get('entry', [])
            for entry in entries:
                for change in entry.get('changes', []):
                    if change.get('field') == 'comments':
                        val = change.get('value', {})
                        comment_id = val.get('id')
                        comment_text = val.get('text', '')
                        media_id = val.get('media', {}).get('id')
                        from_user = val.get('from', {})

                        if comment_id and comment_text:
                            AutomationService.process_comment_event(
                                comment_id=comment_id,
                                username=from_user.get('username', 'user'),
                                comment_text=comment_text,
                                media_id=media_id,
                                commenter_id=from_user.get('id')
                            )

            return JsonResponse({'status': 'EVENT_RECEIVED'}, status=200)
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return HttpResponse("Method not allowed", status=405)


# --- 2. SUPERPROFILE DASHBOARD & UI VIEWS ---

def dashboard_view(request):
    """Main SuperProfile-inspired Dashboard View."""
    is_owner_auth = is_authenticated_owner(request)

    automations = Automation.objects.all().order_by('-created_at')
    accounts = InstagramAccount.objects.filter(is_active=True)

    total_automations = automations.count()
    active_automations = automations.filter(status='ACTIVE').count()
    total_comments = CommentEvent.objects.count()
    total_executions = AutomationExecution.objects.count()
    successful_dms = AutomationExecution.objects.filter(status='SUCCESS', action__action_type='SEND_DM').count()
    total_replies = AutomationExecution.objects.filter(status='SUCCESS', action__action_type='REPLY_COMMENT').count()

    context = {
        'is_owner_authenticated': is_owner_auth,
        'automations': automations,
        'accounts': accounts,
        'total_automations': total_automations,
        'active_automations': active_automations,
        'total_comments': total_comments,
        'total_executions': total_executions,
        'successful_dms': successful_dms,
        'total_replies': total_replies,
        'meta_verify_token': META_VERIFY_TOKEN,
    }
    return render(request, 'instagram/dashboard.html', context)


def automation_list_view(request):
    """List of all automations."""
    automations = Automation.objects.all().order_by('-created_at')
    return render(request, 'instagram/automation_list.html', {'automations': automations})


def automation_create_view(request):
    """Visual Automation Builder (Create)."""
    if request.method == 'POST':
        name = request.POST.get('name', 'New Reel Automation')
        reel_id = request.POST.get('reel_id', '').strip()
        trigger_type = request.POST.get('trigger_type', 'KEYWORD')
        keywords_raw = request.POST.get('keywords', 'guide').split(',')
        reply_text = request.POST.get('reply_text', 'Sent you a DM 📩')
        dm_text = request.POST.get('dm_text', 'Hey {{username}}, here is your requested link: {{link}}')
        resource_url = request.POST.get('resource_url', '').strip()

        account = InstagramAccount.objects.first()
        if not account:
            account = InstagramAccount.objects.create(
                instagram_user_id='demo_ig_123',
                username='pythonkashi',
                access_token='demo_token'
            )

        with transaction.atomic():
            auto = Automation.objects.create(
                instagram_account=account,
                name=name,
                reel_id=reel_id,
                trigger_type=trigger_type,
                status='ACTIVE'
            )

            # Create Trigger
            for kw in keywords_raw:
                if kw.strip():
                    AutomationTrigger.objects.create(
                        automation=auto,
                        keyword=kw.strip(),
                        match_type='CONTAINS'
                    )

            # Create Actions
            if reply_text.strip():
                AutomationAction.objects.create(
                    automation=auto,
                    action_type='REPLY_COMMENT',
                    configuration={'reply_text': reply_text.strip()},
                    order=1
                )

            if dm_text.strip() or resource_url:
                AutomationAction.objects.create(
                    automation=auto,
                    action_type='SEND_DM',
                    configuration={'dm_text': dm_text.strip(), 'resource_url': resource_url},
                    order=2
                )

        return redirect(f"/instagram/automations/{auto.uuid}/")

    return render(request, 'instagram/automation_create.html')


def automation_detail_view(request, uuid):
    """Automation Detail Page showing workflow step diagram & activity."""
    automation = get_object_or_404(Automation, uuid=uuid)
    executions = AutomationExecution.objects.filter(automation=automation).order_by('-executed_at')[:30]

    matched_comments = CommentEvent.objects.filter(automation=automation).count()
    successful_actions = executions.filter(status='SUCCESS').count()

    context = {
        'automation': automation,
        'triggers': automation.triggers.filter(is_active=True),
        'actions': automation.actions.filter(is_active=True).order_by('order'),
        'executions': executions,
        'matched_comments': matched_comments,
        'successful_actions': successful_actions,
    }
    return render(request, 'instagram/automation_detail.html', context)


# --- 3. STATE-CHANGING POST API ENDPOINTS ---

@csrf_exempt
def automation_activate_view(request, uuid):
    if request.method == 'POST':
        auto = get_object_or_404(Automation, uuid=uuid)
        auto.status = 'ACTIVE'
        auto.save()
        return JsonResponse({'success': True, 'status': 'ACTIVE'})
    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def automation_pause_view(request, uuid):
    if request.method == 'POST':
        auto = get_object_or_404(Automation, uuid=uuid)
        auto.status = 'PAUSED'
        auto.save()
        return JsonResponse({'success': True, 'status': 'PAUSED'})
    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def automation_delete_view(request, uuid):
    if request.method == 'POST':
        auto = get_object_or_404(Automation, uuid=uuid)
        auto.delete()
        return JsonResponse({'success': True, 'message': 'Automation deleted'})
    return JsonResponse({'error': 'POST required'}, status=405)


@csrf_exempt
def api_simulate_trigger(request):
    """Simulation Endpoint for instant testing."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            comment_text = data.get('comment_text', 'guide please')
            username = data.get('username', 'student_user')
            comment_id = f"mock_comment_{timezone.now().timestamp()}"

            res = AutomationService.process_comment_event(
                comment_id=comment_id,
                username=username,
                comment_text=comment_text
            )
            return JsonResponse({'success': True, 'result': res})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'error': 'POST required'}, status=405)
