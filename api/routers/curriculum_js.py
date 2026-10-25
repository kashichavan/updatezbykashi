from ninja import Router, Query
from typing import List, Optional
from debugger.curriculum_js import JS_TOPICS
from debugger.javascript_tracer import JavaScriptExecutionTracer
from api.schemas import (
    ChapterSummarySchema,
    ChapterDetailSchema,
    QuizSubmitRequest,
    QuizSubmitResponse,
    CodeExecuteRequest,
    CodeExecuteResponse,
    RoadmapStageSchema
)
from api.auth import AuthBearer # Import AuthBearer
import time
from ninja.errors import HttpError # Import HttpError

router = Router(tags=["JavaScript ES6+ Masterclass Curriculum"])

# Precompute quick chapter index lookup
CHAPTER_INDEX_MAP = {topic["slug"]: idx for idx, topic in enumerate(JS_TOPICS)}

@router.get("/chapters", response=List[ChapterSummarySchema], summary="List all 15 JavaScript Masterclass chapters")
def list_chapters(request, category: Optional[str] = Query(None, description="Filter by category")):
    """
    Fetch all 15 JavaScript ES6+ masterclass curriculum chapters with metadata, reading times, and exercise counts.
    """
    results = []
    for idx, topic in enumerate(JS_TOPICS):
        if category and topic.get("category", "").lower() != category.lower():
            continue

        results.append({
            "order": idx + 1,
            "slug": topic["slug"],
            "title": topic["title"],
            "category": topic.get("category", "Fundamentals"),
            "read_time": topic.get("read_time", "7 min read"),
            "takeaway": topic.get("takeaway", ""),
            "seo_description": topic.get("seo_description", ""),
            "videos_count": len(topic.get("video_tutorials", [])),
            "quizzes_count": len(topic.get("predict_quizzes", [])),
            "challenges_count": len(topic.get("debug_challenges", [])),
        })
    return results

@router.get("/chapters/{slug}", response=ChapterDetailSchema, summary="Get full detailed chapter content by slug")
def get_chapter_detail(request, slug: str):
    """
    Fetch complete Notion-quality interactive chapter content including:
    - Mental Models & V8 AST execution pipelines
    - Annotated Syntax Guides & Starter Code
    - Progressive Real-World Examples & Analogies
    - Common Pitfalls, Rules, and Comparison Matrices
    - Interactive Prediction Quizzes, Debug Challenges & Interview Questions
    - Curated Video Masterclasses from FreeCodeCamp, Chai aur Code, Traversy Media
    """
    if slug not in CHAPTER_INDEX_MAP:
        raise HttpError(404, f"JavaScript Masterclass chapter with slug '{slug}' was not found.")

    idx = CHAPTER_INDEX_MAP[slug]
    topic = JS_TOPICS[idx]

    # Calculate prev & next navigation
    prev_chapter = None
    if idx > 0:
        prev_topic = JS_TOPICS[idx - 1]
        prev_chapter = {
            "slug": prev_topic["slug"],
            "title": prev_topic["title"]
        }

    next_chapter = None
    if idx < len(JS_TOPICS) - 1:
        next_topic = JS_TOPICS[idx + 1]
        next_chapter = {
            "slug": next_topic["slug"],
            "title": next_topic["title"]
        }

    # Format output
    payload = dict(topic)
    payload["order"] = idx + 1
    payload["prev_chapter"] = prev_chapter
    payload["next_chapter"] = next_chapter

    # Ensure required sub-keys exist
    payload.setdefault("progressive_examples", [])
    payload.setdefault("video_tutorials", [])
    payload.setdefault("common_mistakes", [])
    payload.setdefault("rules", [])
    payload.setdefault("practice_exercises", [])
    payload.setdefault("predict_quizzes", [])
    payload.setdefault("debug_challenges", [])
    payload.setdefault("interview_questions", [])
    payload.setdefault("quick_revision", [])

    return payload

@router.post("/execute", response=CodeExecuteResponse, auth=AuthBearer(), summary="Execute and step-trace JavaScript code")
def execute_javascript_code(request, payload: CodeExecuteRequest):
    """
    Execute given JavaScript code and return a step-by-step trace of its execution.
    Requires JWT authentication.
    """
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    tracer = JavaScriptExecutionTracer(payload.code)
    start_time = time.perf_counter()
    result = tracer.run()
    end_time = time.perf_counter()

    return CodeExecuteResponse(
        success=not result.get("error"),
        total_steps=len(result.get("steps", [])),
        execution_time_ms=(end_time - start_time) * 1000,
        output=result.get("output", ""),
        steps=result.get("steps", []),
        error=result.get("error"),
    )

@router.post("/quiz/submit", response=QuizSubmitResponse, auth=AuthBearer(), summary="Submit quiz answer")
def submit_quiz_answer(request, payload: QuizSubmitRequest):
    """
    Submit an answer to a quiz and get immediate feedback on correctness and explanation.
    Requires JWT authentication.
    """
    if not request.auth: 
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    if payload.chapter_slug not in CHAPTER_INDEX_MAP:
        raise HttpError(404, "Chapter not found.")

    chapter = JS_TOPICS[CHAPTER_INDEX_MAP[payload.chapter_slug]]
    quizzes = chapter.get("predict_quizzes", [])

    if payload.quiz_index >= len(quizzes):
        raise HttpError(404, "Quiz not found.")

    quiz = quizzes[payload.quiz_index]
    is_correct = quiz["answer"] == payload.selected_option

    return {"is_correct": is_correct, "correct_answer": quiz["answer"], "explanation": quiz["explanation"]}

@router.get("/roadmap", response=List[RoadmapStageSchema], summary="Get JavaScript curriculum roadmap")
def get_roadmap(request):
    """
    Fetch the structured 7-stage learning roadmap for the JavaScript Masterclass.
    """
    # This data would ideally come from a DB, but for now it's hardcoded in JS_TOPICS
    # We need to process JS_TOPICS to extract roadmap stages based on a 'stage' key or similar.
    # For this example, let's assume a simple structure from JS_TOPICS that can be mapped to RoadmapStageSchema
    
    # Example of a simplified roadmap structure (needs to be derived from JS_TOPICS more robustly)
    # For now, let's mock it or map it directly from JS_TOPICS if structure allows
    # Given JS_TOPICS is a list of dicts, and a `RoadmapStage` has `chapters` which are `ChapterSummary`
    # It implies JS_TOPICS needs some 'stage_number', 'stage_title' and 'badge_color' field if it is to truly map to RoadmapStageSchema
    # As JS_TOPICS is from debugger.curriculum_js, we should not modify it directly.
    # Let's assume there's a separate definition for roadmap stages for now, or create one.

    # For demonstration, I will simulate it based on categories or a simple split for now.
    # In a real app, this would be a separate model/data source.

    stages_data = [
        {
            "stage_number": 1,
            "stage_title": "JavaScript Fundamentals",
            "badge_color": "#38bdf8",
            "description": "Core concepts of JavaScript, variables, data types, and control flow.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "Fundamentals"]
        },
        {
            "stage_number": 2,
            "stage_title": "Functions & Scope",
            "badge_color": "#10b981",
            "description": "Deep dive into functions, lexical scope, closures, and `this` keyword.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "Functions & Scope"]
        },
        {
            "stage_number": 3,
            "stage_title": "Object-Oriented JS",
            "badge_color": "#f59e0b",
            "description": "Prototypes, classes, inheritance, and object composition patterns.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "OOP"]
        },
        {
            "stage_number": 4,
            "stage_title": "Asynchronous JavaScript",
            "badge_color": "#ef4444",
            "description": "Callbacks, Promises, Async/Await, and event loop mechanics.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "Async JS"]
        },
        {
            "stage_number": 5,
            "stage_title": "Modern ES6+",
            "badge_color": "#818cf8",
            "description": "Destructuring, spread/rest, modules, iterators, and generators.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "ES6+"]
        },
        {
            "stage_number": 6,
            "stage_title": "Advanced Topics",
            "badge_color": "#f472b6",
            "description": "Proxies, Reflect, Web Workers, and advanced design patterns.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "Advanced"]
        },
        {
            "stage_number": 7,
            "stage_title": "V8 & Runtime Deep Dive",
            "badge_color": "#14b8a6",
            "description": "Understanding the V8 engine, AST, JIT compilation, and garbage collection.",
            "chapters": [c for c in list_chapters(request) if c["category"] == "V8 Internals"]
        },
    ]
    return stages_data
