import json
import logging
import re
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import InstagramAccount, AutomationRule, AutomationLog
from .services import MetaInstagramClient

logger = logging.getLogger(__name__)

# --- 1. WEBHOOK VERIFICATION & EVENT HANDLER ---

META_VERIFY_TOKEN = '8722183087'

@csrf_exempt
def meta_webhook_endpoint(request):
    """
    Handles Meta Webhook verification (GET) and incoming comment events (POST).
    Endpoint: /instagram/api/instagram/webhook/
    """
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        if mode == 'subscribe' and token == META_VERIFY_TOKEN:
            logger.info("Meta Webhook successfully verified!")
            return HttpResponse(challenge, status=200)
        else:
            logger.warning("Meta Webhook verification token mismatch.")
            return HttpResponse("Verification failed", status=403)

    elif request.method == 'POST':
        try:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            logger.info(f"Received Meta Webhook Event: {data}")

            entries = data.get('entry', [])
            for entry in entries:
                changes = entry.get('changes', [])
                for change in changes:
                    field = change.get('field')
                    value = change.get('value', {})

                    # Handle comment events on Reels / Posts
                    if field == 'comments':
                        process_comment_webhook(value)

            return JsonResponse({'status': 'EVENT_RECEIVED'}, status=200)

        except Exception as e:
            logger.error(f"Error parsing Webhook payload: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return HttpResponse("Method not allowed", status=405)


def process_comment_webhook(val):
    """
    Processes incoming comment payload and matches against active Automation Rules.
    """
    comment_id = val.get('id')
    comment_text = val.get('text', '')
    media_id = val.get('media', {}).get('id')
    from_user = val.get('from', {})
    commenter_id = from_user.get('id')
    commenter_username = from_user.get('username', 'user')

    if not comment_id or not comment_text:
        return

    # Fetch active automation rules
    active_rules = AutomationRule.objects.filter(is_active=True)
    matched_rule = None

    for rule in active_rules:
        # Check target scope (All Reels vs Specific Reel)
        if rule.target_scope == 'SPECIFIC_REEL' and rule.reel_url_or_id:
            if media_id and media_id not in rule.reel_url_or_id and rule.reel_url_or_id not in media_id:
                continue

        # Check trigger keyword
        keyword = rule.trigger_keyword.strip().lower()
        if keyword in comment_text.lower():
            matched_rule = rule
            break

    if not matched_rule:
        # Log unmatched comment
        AutomationLog.objects.create(
            comment_id=comment_id,
            commenter_username=commenter_username,
            commenter_id=commenter_id,
            media_id=media_id,
            comment_text=comment_text,
            status='IGNORED',
            response_details="Keyword did not match any active rule."
        )
        return

    # Execute Rule
    client = MetaInstagramClient(access_token=matched_rule.account.page_access_token if matched_rule.account else None)

    # 1. Post Public Comment Reply
    if matched_rule.comment_reply_text:
        reply_msg = matched_rule.comment_reply_text.replace('{username}', commenter_username)
        client.post_comment_reply(comment_id, reply_msg)

    # 2. Check Follower Gate & Send Private DM
    if matched_rule.enforce_follower_gate:
        is_following = client.check_is_following(commenter_id, matched_rule.account.account_id if matched_rule.account else 'me')
        if not is_following:
            gate_msg = matched_rule.follower_gate_message.replace('{account_username}', matched_rule.account.username if matched_rule.account else 'us')
            client.send_private_dm(commenter_id, gate_msg)
            AutomationLog.objects.create(
                rule=matched_rule,
                comment_id=comment_id,
                commenter_username=commenter_username,
                commenter_id=commenter_id,
                media_id=media_id,
                comment_text=comment_text,
                status='GATE_SENT',
                response_details="Follower Gate triggered. Sent follow prompt DM."
            )
            matched_rule.trigger_count += 1
            matched_rule.save()
            return

    # Deliver Resource Link / Private DM
    dm_body = matched_rule.private_dm_text
    if matched_rule.resource_url:
        dm_body += f"\n\n🔗 Direct Link: {matched_rule.resource_url}"

    dm_res = client.send_private_dm(commenter_id, dm_body)

    status_code = 'SUCCESS' if dm_res.get('success') else 'FAILED'
    AutomationLog.objects.create(
        rule=matched_rule,
        comment_id=comment_id,
        commenter_username=commenter_username,
        commenter_id=commenter_id,
        media_id=media_id,
        comment_text=comment_text,
        status=status_code,
        response_details=json.dumps(dm_res)
    )

    matched_rule.trigger_count += 1
    matched_rule.save()


# --- 2. MOBILE-FIRST UI DASHBOARD VIEWS ---

from requirements.views import is_authenticated_owner

def insta_dashboard_view(request):
    """
    Renders the Mobile-First Instagram Automation Dashboard.
    Requires Owner Login. Route: /instagram/
    """
    is_owner_auth = is_authenticated_owner(request)

    rules = AutomationRule.objects.all().order_by('-created_at')
    logs = AutomationLog.objects.all()[:30]
    accounts = InstagramAccount.objects.filter(is_active=True)

    total_triggers = sum(r.trigger_count for r in rules)
    total_logs = AutomationLog.objects.count()
    success_logs = AutomationLog.objects.filter(status='SUCCESS').count()

    context = {
        'is_owner_authenticated': is_owner_auth,
        'rules': rules,
        'logs': logs,
        'accounts': accounts,
        'total_rules': rules.count(),
        'total_triggers': total_triggers,
        'total_logs': total_logs,
        'success_logs': success_logs,
        'meta_verify_token': META_VERIFY_TOKEN,
    }
    return render(request, 'instagram/dashboard.html', context)


# --- 3. REST API ENDPOINTS FOR DASHBOARD UI ---

@csrf_exempt
def api_rules_list_create(request):
    """
    API endpoint to list or create automation rules.
    Route: /instagram/api/rules/
    """
    if request.method == 'GET':
        rules = AutomationRule.objects.all().order_by('-created_at')
        rules_data = []
        for r in rules:
            rules_data.append({
                'uuid': str(r.uuid),
                'id': r.id,
                'name': r.name,
                'target_scope': r.target_scope,
                'target_scope_display': r.get_target_scope_display(),
                'reel_url_or_id': r.reel_url_or_id or '',
                'trigger_keyword': r.trigger_keyword,
                'comment_reply_text': r.comment_reply_text,
                'private_dm_text': r.private_dm_text,
                'resource_url': r.resource_url or '',
                'enforce_follower_gate': r.enforce_follower_gate,
                'is_active': r.is_active,
                'trigger_count': r.trigger_count,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            })
        return JsonResponse({'success': True, 'rules': rules_data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            rule = AutomationRule.objects.create(
                name=data.get('name', 'New Automation Rule'),
                target_scope=data.get('target_scope', 'ALL_REELS'),
                reel_url_or_id=data.get('reel_url_or_id', '').strip(),
                trigger_keyword=data.get('trigger_keyword', 'python').strip(),
                comment_reply_text=data.get('comment_reply_text', 'Thanks @{username}! 👋 Check your DM.'),
                private_dm_text=data.get('private_dm_text', 'Here is your direct access link!'),
                resource_url=data.get('resource_url', '').strip(),
                enforce_follower_gate=data.get('enforce_follower_gate', True),
                is_active=data.get('is_active', True)
            )
            return JsonResponse({'success': True, 'message': 'Automation Rule Created Successfully!', 'rule_id': rule.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_rule_toggle_delete(request, rule_id):
    """
    API endpoint to toggle active status or delete a rule.
    Route: /instagram/api/rules/<rule_id>/
    """
    try:
        rule = AutomationRule.objects.get(id=rule_id)
    except AutomationRule.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Rule not found'}, status=404)

    if request.method == 'POST':
        rule.is_active = not rule.is_active
        rule.save()
        return JsonResponse({'success': True, 'is_active': rule.is_active})

    elif request.method == 'DELETE':
        rule.delete()
        return JsonResponse({'success': True, 'message': 'Rule deleted successfully.'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_logs_list(request):
    """
    API endpoint to fetch latest webhook execution logs.
    Route: /instagram/api/logs/
    """
    logs = AutomationLog.objects.all()[:50]
    logs_data = []
    for l in logs:
        logs_data.append({
            'uuid': str(l.uuid),
            'rule_name': l.rule.name if l.rule else 'Default / Unmatched',
            'comment_id': l.comment_id,
            'commenter_username': l.commenter_username,
            'comment_text': l.comment_text,
            'status': l.status,
            'status_display': l.get_status_display(),
            'response_details': l.response_details,
            'created_at': l.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse({'success': True, 'logs': logs_data})


@csrf_exempt
def api_simulate_trigger(request):
    """
    Simulation API to test reel comment automation rules instantly from Dashboard.
    Route: /instagram/api/simulate/
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            comment_text = data.get('comment_text', 'python')
            commenter_username = data.get('commenter_username', 'student_user')
            media_id = data.get('media_id', 'reel_123456')

            mock_val = {
                'id': f"comment_{timezone.now().timestamp()}",
                'text': comment_text,
                'media': {'id': media_id},
                'from': {
                    'id': f"user_{timezone.now().timestamp()}",
                    'username': commenter_username
                }
            }

            process_comment_webhook(mock_val)
            return JsonResponse({'success': True, 'message': f"Simulated comment '{comment_text}' by @{commenter_username} successfully!"})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
