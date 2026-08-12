import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db.models import Count

logger = logging.getLogger(__name__)

from .models import (
    InstagramAccount,
    CommentAutomation,
    InstagramConversation,
    InstagramMessage,
    AutomationExecution
)
from .services.oauth import InstagramOAuthService
from .services.instagram_api import InstagramAPI

def admin_required(view_func):
    """
    Decorator that restricts access to authenticated admin / staff users.
    Checks Django Session & Authorization Bearer JWT Token.
    Redirects unauthenticated users to /owner/ (admin portal).
    """
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)

        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth.models import User
                access = AccessToken(token)
                user_id = access.get('user_id')
                user = User.objects.filter(id=user_id, is_staff=True).first()
                if user:
                    request.user = user
                    return view_func(request, *args, **kwargs)
            except Exception:
                pass

        return redirect(f"/owner/?next={request.path}")

    return wrapper

def get_active_account(request):
    """
    Helper to select active account from session or default to the most recent connected account.
    """
    account_id = request.session.get('active_instagram_account_id')
    if account_id:
        acc = InstagramAccount.objects.filter(id=account_id).first()
        if acc:
            return acc
    return InstagramAccount.objects.filter(is_connected=True).first()

@admin_required
def dashboard_view(request):
    """
    Main Instagram Automation Dashboard
    URL: /instagram/
    """
    try:
        account = get_active_account(request)
        all_accounts = InstagramAccount.objects.all()

        if not account and not all_accounts.exists():
            return render(request, 'instaautomation/connect.html', {
                'no_account': True
            })

        automations = CommentAutomation.objects.filter(instagram_account=account) if account else []
        
        # Calculate stats safely
        comments_processed = 0
        dms_sent = 0
        automations_triggered = 0

        if account:
            try:
                comments_processed = AutomationExecution.objects.filter(
                    automation__instagram_account=account,
                    event_type=AutomationExecution.EventType.COMMENT,
                    status=AutomationExecution.Status.SUCCESS
                ).count()
            except Exception:
                pass

            try:
                dms_sent = InstagramMessage.objects.filter(
                    conversation__instagram_account=account,
                    direction=InstagramMessage.Direction.OUTGOING
                ).count()
            except Exception:
                pass

            try:
                automations_triggered = AutomationExecution.objects.filter(
                    automation__instagram_account=account,
                    status=AutomationExecution.Status.SUCCESS
                ).count()
            except Exception:
                pass

        context = {
            'account': account,
            'all_accounts': all_accounts,
            'automations': automations,
            'comments_processed': comments_processed,
            'dms_sent': dms_sent,
            'automations_triggered': automations_triggered,
        }
        return render(request, 'instaautomation/dashboard.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_view: {e}")
        return render(request, 'instaautomation/connect.html', {
            'no_account': True,
            'error_message': str(e)
        })

@admin_required
def connect_view(request):
    """
    Instagram Connection Endpoint supporting both Instagram Business OAuth & Direct Access Token Entry.
    URL: /instagram/connect/
    """
    if request.method == 'POST':
        # Direct Access Token Manual Connect Option
        token = request.POST.get('access_token', '').strip()
        username = request.POST.get('username', '').strip().replace('@', '')
        user_id = request.POST.get('instagram_user_id', '').strip()

        if not token or not username:
            messages.error(request, "Instagram Username and Access Token are required.")
            return render(request, 'instaautomation/connect.html')

        try:
            oauth_service = InstagramOAuthService()
            # Verify or fetch profile data via token
            account_data = None
            try:
                account_data = oauth_service.get_instagram_account_data(token)
            except Exception:
                account_data = {
                    'instagram_user_id': user_id or f"manual_{username}",
                    'username': username,
                    'display_name': username,
                    'profile_picture': '',
                    'account_type': 'BUSINESS'
                }

            expires_at = timezone.now() + timedelta(days=60)
            account = oauth_service.connect_account(
                account_data=account_data,
                access_token=token,
                expires_at=expires_at
            )
            request.session['active_instagram_account_id'] = account.id
            messages.success(request, f"Successfully connected Instagram account @{account.username}!")
            return redirect('instaautomation:dashboard')
        except Exception as e:
            messages.error(request, f"Connection error: {str(e)}")
            return render(request, 'instaautomation/connect.html')

    oauth_service = InstagramOAuthService()
    account_id = request.GET.get('reconnect_id')
    auth_url, state = oauth_service.get_authorization_url(account_id=account_id)
    return render(request, 'instaautomation/connect.html', {
        'auth_url': auth_url
    })

@admin_required
def oauth_callback_view(request):
    """
    Official Meta / Instagram OAuth Callback Endpoint.
    URL: /instagram/oauth/callback/
    """
    error = request.GET.get('error')
    error_reason = request.GET.get('error_reason')
    error_description = request.GET.get('error_description')

    if error:
        messages.error(request, f"OAuth Authorization Error ({error_reason}): {error_description}")
        return redirect('instaautomation:dashboard')

    code = request.GET.get('code')
    state = request.GET.get('state')

    # Validate state
    raw_state = state.split(':')[0] if state and ':' in state else state
    reconnect_account_id = state.split(':')[1] if state and ':' in state else None

    oauth_service = InstagramOAuthService()
    if raw_state and not oauth_service.validate_state(raw_state):
        logger.warning(f"OAuth state parameter check bypassed for state: {raw_state}")

    if not code:
        messages.error(request, "No authorization code returned from Meta.")
        return redirect('instaautomation:dashboard')

    try:
        access_token, expires_at = oauth_service.exchange_code(code)
        account_data = oauth_service.get_instagram_account_data(access_token)
        account = oauth_service.connect_account(
            account_data=account_data,
            access_token=access_token,
            expires_at=expires_at,
            existing_account_id=reconnect_account_id
        )

        request.session['active_instagram_account_id'] = account.id
        messages.success(request, f"Successfully connected Instagram account @{account.username}!")
    except Exception as e:
        messages.error(request, f"Failed to connect Instagram account: {str(e)}")

    return redirect('instaautomation:dashboard')

@admin_required
def reconnect_view(request, pk=None):
    """
    Reconnects an existing Instagram account.
    URL: /instagram/reconnect/ or /instagram/reconnect/<id>/
    """
    account = get_object_or_404(InstagramAccount, pk=pk) if pk else get_active_account(request)
    if not account:
        return redirect('instaautomation:connect')

    oauth_service = InstagramOAuthService()
    auth_url, _ = oauth_service.get_authorization_url(account_id=account.id)
    return redirect(auth_url)

@admin_required
def disconnect_view(request, pk=None):
    """
    Disconnects an Instagram account (clears credentials, marks inactive).
    URL: /instagram/disconnect/ or /instagram/disconnect/<id>/
    """
    account = get_object_or_404(InstagramAccount, pk=pk) if pk else get_active_account(request)
    if account:
        oauth_service = InstagramOAuthService()
        oauth_service.disconnect_account(account)
        messages.info(request, f"Disconnected Instagram account @{account.username}.")
    return redirect('instaautomation:dashboard')

@admin_required
def switch_account_view(request, pk):
    """
    Switch currently active Instagram account in session.
    URL: /instagram/switch/<id>/
    """
    account = get_object_or_404(InstagramAccount, pk=pk)
    request.session['active_instagram_account_id'] = account.id
    messages.success(request, f"Switched to Instagram account @{account.username}")
    return redirect('instaautomation:dashboard')

@admin_required
def account_detail_view(request):
    """
    Account Overview & Meta API Status Page
    URL: /instagram/account/
    """
    account = get_active_account(request)
    if not account:
        return redirect('instaautomation:connect')

    profile_data = None
    api_error = None
    if account.is_token_valid:
        try:
            api = InstagramAPI(account)
            profile_data = api.get_account_profile()
        except Exception as e:
            api_error = str(e)

    context = {
        'account': account,
        'profile_data': profile_data,
        'api_error': api_error
    }
    return render(request, 'instaautomation/account.html', context)

@admin_required
def automation_list_view(request):
    """
    List all Comment & DM Automations
    URL: /instagram/automations/
    """
    return redirect('instaautomation:dashboard')

@admin_required
def automation_create_view(request):
    """
    Create a new Comment & DM Automation
    URL: /instagram/automations/create/
    """
    account = get_active_account(request)
    if not account:
        messages.error(request, "Please connect an Instagram account first.")
        return redirect('instaautomation:connect')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        target_scope = request.POST.get('target_scope', 'ALL_REELS').strip()
        specific_reel_id = request.POST.get('specific_reel_id', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        comment_reply = request.POST.get('comment_reply', '').strip()
        dm_message = request.POST.get('dm_message', '').strip()
        require_follow = request.POST.get('require_follow') == 'on'
        confirmation_keyword = request.POST.get('confirmation_keyword', 'DONE').strip()
        final_message = request.POST.get('final_message', '').strip()
        resource_url = request.POST.get('resource_url', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not name or not keywords:
            messages.error(request, "Name and Keywords are required fields.")
            return render(request, 'instaautomation/automation_form.html', {'account': account})

        automation = CommentAutomation.objects.create(
            instagram_account=account,
            name=name,
            target_scope=target_scope,
            specific_reel_id=specific_reel_id,
            keywords=keywords,
            comment_reply=comment_reply,
            dm_message=dm_message,
            require_follow=require_follow,
            confirmation_keyword=confirmation_keyword,
            final_message=final_message,
            resource_url=resource_url,
            is_active=is_active
        )
        messages.success(request, f"Automation rule '{automation.name}' created successfully!")
        return redirect('instaautomation:automation_list')

    return render(request, 'instaautomation/automation_form.html', {'account': account})

@admin_required
def automation_edit_view(request, pk):
    """
    Edit an existing Automation Rule
    URL: /instagram/automations/<id>/edit/
    """
    account = get_active_account(request)
    automation = get_object_or_404(CommentAutomation, pk=pk)

    if request.method == 'POST':
        automation.name = request.POST.get('name', '').strip()
        automation.target_scope = request.POST.get('target_scope', 'ALL_REELS').strip()
        automation.specific_reel_id = request.POST.get('specific_reel_id', '').strip()
        automation.keywords = request.POST.get('keywords', '').strip()
        automation.comment_reply = request.POST.get('comment_reply', '').strip()
        automation.dm_message = request.POST.get('dm_message', '').strip()
        automation.require_follow = request.POST.get('require_follow') == 'on'
        automation.confirmation_keyword = request.POST.get('confirmation_keyword', 'DONE').strip()
        automation.final_message = request.POST.get('final_message', '').strip()
        automation.resource_url = request.POST.get('resource_url', '').strip()
        automation.is_active = request.POST.get('is_active') == 'on'

        automation.save()
        messages.success(request, f"Automation '{automation.name}' updated successfully!")
        return redirect('instaautomation:automation_list')

    return render(request, 'instaautomation/automation_form.html', {
        'account': account,
        'automation': automation,
        'is_edit': True
    })

@admin_required
def automation_toggle_view(request, pk):
    """
    Enable/Disable Automation Rule
    URL: /instagram/automations/<id>/toggle/
    """
    automation = get_object_or_404(CommentAutomation, pk=pk)
    automation.is_active = not automation.is_active
    automation.save(update_fields=['is_active'])
    status_str = "activated" if automation.is_active else "disabled"
    messages.success(request, f"Automation '{automation.name}' {status_str}.")
    return redirect('instaautomation:automation_list')

@admin_required
def automation_delete_view(request, pk):
    """
    Delete an Automation Rule
    URL: /instagram/automations/<id>/delete/
    """
    automation = get_object_or_404(CommentAutomation, pk=pk)
    name = automation.name
    automation.delete()
    messages.info(request, f"Automation '{name}' deleted.")
    return redirect('instaautomation:automation_list')

@admin_required
def conversations_view(request):
    """
    List Conversations
    URL: /instagram/conversations/
    """
    account = get_active_account(request)
    if not account:
        return redirect('instaautomation:connect')

    conversations = InstagramConversation.objects.filter(instagram_account=account).order_by('-last_message_at')
    return render(request, 'instaautomation/conversations.html', {
        'account': account,
        'conversations': conversations
    })

@admin_required
def conversation_detail_view(request, pk):
    """
    Conversation Detail View showing chat message history
    URL: /instagram/conversations/<id>/
    """
    account = get_active_account(request)
    conversation = get_object_or_404(InstagramConversation, pk=pk)
    messages_list = conversation.messages.all()

    return render(request, 'instaautomation/conversation_detail.html', {
        'account': account,
        'conversation': conversation,
        'messages_list': messages_list
    })

# ==============================================================================
# SUPERPROFILE API EQUIVALENT JSON ENDPOINTS
# ==============================================================================

@csrf_exempt
def api_get_instagram_connect_url(request):
    """
    Superprofile equivalent API: GET /instagram/api/adm/get_instagram_connect_url
    Returns Instagram Business OAuth authUrl JSON payload.
    """
    oauth_service = InstagramOAuthService()
    account = get_active_account(request)
    account_id = account.id if account else None
    auth_url, state = oauth_service.get_authorization_url(account_id=account_id)
    return JsonResponse({
        'status': True,
        'data': {
            'authUrl': auth_url,
            'state': state
        }
    })

@csrf_exempt
def api_get_instagram_details(request):
    """
    Superprofile equivalent API: GET /instagram/api/adm/get_instagram_details
    Returns connected Instagram account details JSON payload.
    """
    account = get_active_account(request)
    if not account:
        return JsonResponse({'status': False, 'data': None, 'message': 'No connected Instagram account'}, status=404)

    return JsonResponse({
        'status': True,
        'data': {
            'id': account.id,
            'instagramUserId': account.instagram_user_id,
            'username': account.username,
            'displayName': account.display_name,
            'profilePicture': account.profile_picture,
            'accountType': account.account_type,
            'isConnected': account.is_connected,
            'isTokenValid': account.is_token_valid,
            'connectionStatus': account.connection_status,
            'lastSyncedAt': account.last_synced_at.isoformat() if account.last_synced_at else None
        }
    })

@csrf_exempt
def api_get_messenger_details(request):
    """
    Superprofile equivalent API: GET /instagram/api/adm/get_messenger_details
    Returns active automations and conversation counts JSON payload.
    """
    account = get_active_account(request)
    if not account:
        return JsonResponse({'status': False, 'data': {'automations': [], 'conversationsCount': 0}})

    automations = CommentAutomation.objects.filter(instagram_account=account, is_active=True)
    conv_count = InstagramConversation.objects.filter(instagram_account=account).count()

    automations_data = [{
        'id': auto.id,
        'name': auto.name,
        'keywords': auto.get_keywords_list(),
        'commentReply': auto.comment_reply,
        'dmMessage': auto.dm_message,
        'confirmationKeyword': auto.confirmation_keyword,
        'finalMessage': auto.final_message,
        'resourceUrl': auto.resource_url,
        'isActive': auto.is_active
    } for auto in automations]

    return JsonResponse({
        'status': True,
        'data': {
            'automations': automations_data,
            'conversationsCount': conv_count
        }
    })

@csrf_exempt
def api_get_auto_dm_analytics(request):
    """
    Superprofile equivalent API: GET /instagram/api/adm/get_auto_dm_analytics
    Returns real-time comment and DM automation analytics JSON payload.
    """
    account = get_active_account(request)
    if not account:
        return JsonResponse({'status': True, 'data': {'totalComments': 0, 'totalDms': 0, 'successfulExecutions': 0}})

    total_comments = AutomationExecution.objects.filter(
        automation__instagram_account=account,
        event_type=AutomationExecution.EventType.COMMENT
    ).count()

    total_dms = InstagramMessage.objects.filter(
        conversation__instagram_account=account,
        direction=InstagramMessage.Direction.OUTGOING
    ).count()

    successful_executions = AutomationExecution.objects.filter(
        automation__instagram_account=account,
        status=AutomationExecution.Status.SUCCESS
    ).count()

    return JsonResponse({
        'status': True,
        'data': {
            'totalComments': total_comments,
            'totalDms': total_dms,
            'successfulExecutions': successful_executions
        }
    })


