"""Owner portal: Instagram "doesn't follow back" tracker (see services/ig_followers.py)."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services import ig_followers
from .views import is_authenticated_owner

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def _deny():
    return JsonResponse({'error': 'Unauthorized. Owner login required.'}, status=401)


def _no_store(resp):
    resp['Cache-Control'] = 'no-store'
    return resp


@csrf_exempt
def api_ig_followers(request):
    if not is_authenticated_owner(request)[0]:
        return _deny()
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    return _no_store(JsonResponse(ig_followers.build_state()))


@csrf_exempt
def api_ig_followers_import(request):
    if not is_authenticated_owner(request)[0]:
        return _deny()
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'error': 'Choose the .zip file Instagram emailed you.'}, status=400)
    if upload.size > MAX_UPLOAD_BYTES:
        return JsonResponse({'error': 'That file is over 25 MB. Request only "Followers and following" in the download.'}, status=400)
    try:
        snap, requeued = ig_followers.import_snapshot(upload)
    except ig_followers.ExportError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    state = ig_followers.build_state()
    state['imported'] = {'followers': snap.followers_count, 'following': snap.following_count, 'requeued': requeued}
    return _no_store(JsonResponse(state))


@csrf_exempt
def api_ig_followers_mark(request):
    if not is_authenticated_owner(request)[0]:
        return _deny()
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    try:
        body = json.loads(request.body or b'{}')
        ig_followers.mark(body.get('username'), body.get('action'))
    except (ValueError, TypeError) as exc:
        return JsonResponse({'error': str(exc) or 'Bad request.'}, status=400)
    return _no_store(JsonResponse(ig_followers.build_state()))
