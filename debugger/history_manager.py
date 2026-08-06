from .models import DebugSession

class SessionHistoryManager:
    """
    Session History & Replay Manager.
    Handles listing past execution sessions and restoring execution snapshots.
    """

    @staticmethod
    def get_recent_sessions(limit=10):
        sessions = DebugSession.objects.all().order_by('-created_at')[:limit]
        return [
            {
                'session_id': str(s.session_id),
                'language': s.language,
                'total_steps': s.total_steps,
                'snippet_title': s.snippet.title if s.snippet else f"Program ({s.language})",
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for s in sessions
        ]
