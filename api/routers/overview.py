from ninja import Router
from api.schemas import CurriculumOverviewSchema
from debugger.curriculum_js import JS_TOPICS
from debugger.curriculum_python import PYTHON_TOPICS
from debugger.curriculum_java import JAVA_TOPICS

router = Router(tags=["Platform & Curriculum Overview"])

@router.get("/overview", response=CurriculumOverviewSchema, summary="Get platform curriculum statistics")
def get_curriculum_overview(request):
    """
    Get aggregated counts for all masterclass chapters (Python, Java, JavaScript), SQL sandboxes, quizzes, and videos.
    """
    total_js_quizzes = sum(len(t.get("predict_quizzes", [])) for t in JS_TOPICS)
    total_js_challenges = sum(len(t.get("debug_challenges", [])) for t in JS_TOPICS)
    total_js_videos = sum(len(t.get("video_tutorials", [])) for t in JS_TOPICS)

    total_py_quizzes = sum(len(t.get("predict_quizzes", [])) for t in PYTHON_TOPICS) if 'PYTHON_TOPICS' in globals() else 0
    total_py_challenges = sum(len(t.get("debug_challenges", [])) for t in PYTHON_TOPICS) if 'PYTHON_TOPICS' in globals() else 0

    categories = list(set(t.get("category", "Fundamentals") for t in JS_TOPICS))
    categories.sort()

    return {
        "total_javascript_chapters": len(JS_TOPICS),
        "total_python_chapters": len(PYTHON_TOPICS),
        "total_java_chapters": len(JAVA_TOPICS),
        "total_sql_datasets": 6,
        "total_practice_quizzes": total_js_quizzes + total_py_quizzes,
        "total_debug_challenges": total_js_challenges + total_py_challenges,
        "total_video_tutorials": total_js_videos,
        "categories": categories
    }
