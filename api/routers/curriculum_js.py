from ninja import Router, Query
from django.shortcuts import get_object_or_404
from typing import List, Optional, Dict, Any
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
import time

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
        from ninja.errors import HttpError
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

@router.post("/execute", response=CodeExecuteResponse, summary="Execute and step-trace JavaScript code")
def execute_javascript_code(request, payload: CodeExecuteRequest):
    """
    Execute arbitrary JavaScript source code through the V8 AST Line-by-Line Execution Tracer.
    Returns call stack frames, variable state deltas, heap pointers, and AI explanation per step.
    """
    code = payload.code or ""
    if not code.strip():
        return {
            "success": False,
            "total_steps": 0,
            "execution_time_ms": 0.0,
            "output": "",
            "steps": [],
            "error": "Code content is empty."
        }

    t0 = time.perf_counter()
    try:
        tracer = JavaScriptExecutionTracer(code)
        trace_data = tracer.execute()
        exec_ms = round((time.perf_counter() - t0) * 1000, 2)

        formatted_steps = []
        for step in trace_data.get("steps", []):
            formatted_steps.append({
                "step": step.get("step_index", 0),
                "line_number": step.get("line_number", 1),
                "event": step.get("event_type", "line"),
                "func_name": step.get("fn_name"),
                "call_stack": step.get("stack_frames", ["global()"]),
                "variables": step.get("variables", {}),
                "stdout_buffer": step.get("stdout", ""),
                "heap_objects": {},
                "explanation": step.get("ai_explanation", "")
            })

        full_stdout = "\n".join(tracer.stdout_lines)
        return {
            "success": True,
            "total_steps": len(formatted_steps),
            "execution_time_ms": exec_ms,
            "output": full_stdout,
            "steps": formatted_steps,
            "error": None
        }
    except Exception as e:
        exec_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "success": False,
            "total_steps": 0,
            "execution_time_ms": exec_ms,
            "output": "",
            "steps": [],
            "error": f"Execution error: {str(e)}"
        }

@router.post("/quiz/submit", response=QuizSubmitResponse, summary="Submit and verify quiz answer")
def submit_quiz_answer(request, payload: QuizSubmitRequest):
    """
    Verify user selected answer for an interactive chapter prediction quiz and return the canonical explanation.
    """
    if payload.chapter_slug not in CHAPTER_INDEX_MAP:
        from ninja.errors import HttpError
        raise HttpError(404, f"Chapter '{payload.chapter_slug}' not found.")

    idx = CHAPTER_INDEX_MAP[payload.chapter_slug]
    topic = JS_TOPICS[idx]
    quizzes = topic.get("predict_quizzes", [])

    if payload.quiz_index < 0 or payload.quiz_index >= len(quizzes):
        from ninja.errors import HttpError
        raise HttpError(400, f"Invalid quiz index {payload.quiz_index}.")

    quiz = quizzes[payload.quiz_index]
    canonical_answer = quiz.get("answer", "")
    explanation = quiz.get("explanation", "")

    # Compare options cleanly
    user_choice = payload.selected_option.strip().lower()
    clean_canon = canonical_answer.strip().lower()

    # Extract letter (A, B, C, D) if present
    is_correct = (user_choice == clean_canon) or (
        len(user_choice) > 0 and clean_canon.startswith(user_choice[:1])
    )

    return {
        "is_correct": is_correct,
        "selected_option": payload.selected_option,
        "correct_answer": canonical_answer,
        "explanation": explanation
    }

@router.get("/roadmap", response=List[RoadmapStageSchema], summary="Get structured 7-stage learning roadmap")
def get_javascript_roadmap(request):
    """
    Get the structured 7-stage learning journey roadmap for Modern JavaScript (ES6+).
    """
    stages_definition = [
        {
            "stage_number": 1,
            "stage_title": "1. Fundamentals & Execution Context",
            "badge_color": "#38bdf8",
            "description": "V8 engine architecture, data types, scoping rules (var vs let vs const), and equality coercion traps.",
            "slugs": [
                "javascript-syntax-variables-datatypes",
                "javascript-var-let-const-hoisting",
                "javascript-operators-type-coercion"
            ]
        },
        {
            "stage_number": 2,
            "stage_title": "2. Control Flow & Iteration Protocols",
            "badge_color": "#10b981",
            "description": "Branching conditionals, switch cases, and loops (for, while, for..of, for..in) with break and continue.",
            "slugs": [
                "javascript-conditionals-switch",
                "javascript-loops-for-while-forof"
            ]
        },
        {
            "stage_number": 3,
            "stage_title": "3. Functions & Scope Architecture",
            "badge_color": "#a855f7",
            "description": "Function declarations vs expressions, arrow functions, and lexical 'this' binding mechanics.",
            "slugs": [
                "javascript-functions-declarations-expressions",
                "javascript-arrow-functions-this"
            ]
        },
        {
            "stage_number": 4,
            "stage_title": "4. Data Structures: Arrays & Objects",
            "badge_color": "#f59e0b",
            "description": "Array methods, functional programming (map, filter, reduce), object modeling, and destructuring.",
            "slugs": [
                "javascript-arrays-methods",
                "javascript-array-hof-map-filter-reduce",
                "javascript-objects-properties-methods",
                "javascript-destructuring-spread-rest"
            ]
        },
        {
            "stage_number": 5,
            "stage_title": "5. Object-Oriented JS & Prototypes",
            "badge_color": "#ec4899",
            "description": "ES6 Classes, constructors, private fields (#), inheritance, prototype chaining, and instance checks.",
            "slugs": [
                "javascript-classes-oop-prototype"
            ]
        },
        {
            "stage_number": 6,
            "stage_title": "6. Lexical Scoping & Closures",
            "badge_color": "#6366f1",
            "description": "Closure encapsulation, private state factories, memory leak prevention, and memoization patterns.",
            "slugs": [
                "javascript-closures-scope-chain"
            ]
        },
        {
            "stage_number": 7,
            "stage_title": "7. Asynchronous JS & The Event Loop",
            "badge_color": "#14b8a6",
            "description": "Promises, async/await, fetch API, Call Stack, Microtasks, Macrotasks, and DOM Event Delegation.",
            "slugs": [
                "javascript-promises-async-await",
                "javascript-dom-events-delegation"
            ]
        }
    ]

    roadmap = []
    for s in stages_definition:
        stage_chapters = []
        for slug in s["slugs"]:
            if slug in CHAPTER_INDEX_MAP:
                idx = CHAPTER_INDEX_MAP[slug]
                t = JS_TOPICS[idx]
                stage_chapters.append({
                    "order": idx + 1,
                    "slug": t["slug"],
                    "title": t["title"],
                    "category": t.get("category", ""),
                    "read_time": t.get("read_time", "7 min read"),
                    "takeaway": t.get("takeaway", ""),
                    "seo_description": t.get("seo_description", ""),
                    "videos_count": len(t.get("video_tutorials", [])),
                    "quizzes_count": len(t.get("predict_quizzes", [])),
                    "challenges_count": len(t.get("debug_challenges", [])),
                })
        
        roadmap.append({
            "stage_number": s["stage_number"],
            "stage_title": s["stage_title"],
            "badge_color": s["badge_color"],
            "description": s["description"],
            "chapters": stage_chapters
        })

    return roadmap
