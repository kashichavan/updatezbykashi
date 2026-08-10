import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db.models import Count

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
    Decorator that restricts access strictly to logged-in admin / staff users.
    Redirects unauthenticated or non-staff users to /owner/ (admin portal).
    """
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url='/owner/'
    )(view_func)

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
    account = get_active_account(request)
    all_accounts = InstagramAccount.objects.all()

    if not account and not all_accounts.exists():
        return render(request, 'instaautomation/connect.html', {
            'no_account': True
        })

    automations = CommentAutomation.objects.filter(instagram_account=account) if account else []
    
    # Calculate stats
    comments_processed = AutomationExecution.objects.filter(
        automation__instagram_account=account,
        event_type=AutomationExecution.EventType.COMMENT,
        status=AutomationExecution.Status.SUCCESS
    ).count() if account else 0

    dms_sent = InstagramMessage.objects.filter(
        conversation__instagram_account=account,
        direction=InstagramMessage.Direction.OUTGOING
    ).count() if account else 0

    automations_triggered = AutomationExecution.objects.filter(
        automation__instagram_account=account,
        status=AutomationExecution.Status.SUCCESS
    ).count() if account else 0

    context = {
        'account': account,
        'all_accounts': all_accounts,
        'automations': automations,
        'comments_processed': comments_processed,
        'dms_sent': dms_sent,
        'automations_triggered': automations_triggered,
    }
    return render(request, 'instaautomation/dashboard.html', context)

@admin_required
def connect_view(request):
    """
    Redirects user to official Meta / Instagram OAuth Login Page.
    URL: /instagram/connect/
    """
    oauth_service = InstagramOAuthService()
    account_id = request.GET.get('reconnect_id')
    auth_url, state = oauth_service.get_authorization_url(account_id=account_id)
    return redirect(auth_url)

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
    if not oauth_service.validate_state(raw_state):
        messages.error(request, "Invalid or expired OAuth state parameter. Security verification failed.")
        return redirect('instaautomation:dashboard')

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
    account = get_active_account(request)
    if not account:
        return redirect('instaautomation:connect')

    automations = CommentAutomation.objects.filter(instagram_account=account)
    return render(request, 'instaautomation/automation_list.html', {
        'account': account,
        'automations': automations
    })

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
        keywords = request.POST.get('keywords', '').strip()
        comment_reply = request.POST.get('comment_reply', '').strip()
        dm_message = request.POST.get('dm_message', '').strip()
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
            keywords=keywords,
            comment_reply=comment_reply,
            dm_message=dm_message,
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
        automation.keywords = request.POST.get('keywords', '').strip()
        automation.comment_reply = request.POST.get('comment_reply', '').strip()
        automation.dm_message = request.POST.get('dm_message', '').strip()
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

