from ninja import Schema
from typing import List, Optional, Any, Dict
from datetime import datetime

# ── 1. BLOG SCHEMAS ──
class CategorySchema(Schema):
    id: int
    name: str
    slug: str
    description: str
    icon: str
    color: str
    order: int
    posts_count: Optional[int] = 0

class TagSchema(Schema):
    id: int
    name: str
    slug: str
    posts_count: Optional[int] = 0

class BlogPostListSchema(Schema):
    id: int
    title: str
    slug: str
    excerpt: str
    cover_image_url: Optional[str] = None
    author_name: str
    author_title: str
    author_avatar_url: Optional[str] = None
    category: Optional[CategorySchema] = None
    tags: List[TagSchema] = []
    read_time_minutes: int
    views_count: int
    likes_count: int
    is_featured: bool
    published_at: datetime

class BlogPostDetailSchema(BlogPostListSchema):
    content: str
    seo_title: str
    seo_description: str
    canonical_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    related_posts: List[BlogPostListSchema] = []

class BlogPostsResponse(Schema):
    total: int
    limit: int
    offset: int
    posts: List[BlogPostListSchema]


# ── 2. JAVASCRIPT MASTERCLASS CURRICULUM SCHEMAS ──
class AnalogyMappingItem(Schema):
    real: str
    prog: str

class AnalogySchema(Schema):
    title: str
    text: str
    mapping: List[AnalogyMappingItem] = []

class ProgressiveExampleSchema(Schema):
    tier: str
    title: str
    description: str
    code: str
    output: Optional[str] = ""
    notes: Optional[str] = ""

class VideoTutorialSchema(Schema):
    title: str
    channel: str
    youtube_id: str
    duration: str
    level: str
    description: str

class CommonMistakeSchema(Schema):
    title: str
    bad: str
    why_bad: str
    good: str
    why_good: str

class RuleSchema(Schema):
    rule: str
    detail: str

class ComparisonRowSchema(Schema):
    feature: str
    val_a: str
    val_b: str

class ComparisonSchema(Schema):
    title: str
    item_a: str
    item_b: str
    rows: List[ComparisonRowSchema] = []

class MiniProjectSchema(Schema):
    title: str
    problem: str
    requirements: List[str] = []
    solution_code: str
    solution_explanation: str

class PracticeExerciseSchema(Schema):
    level: str
    title: str
    prompt: str
    hint: str
    solution: str

class PredictQuizSchema(Schema):
    code: str
    options: List[str]
    answer: str
    explanation: str

class DebugChallengeSchema(Schema):
    context: str
    broken_code: str
    bug_reason: str
    fixed_code: str

class InterviewQuestionSchema(Schema):
    tier: str
    question: str
    answer: str

class FinalChallengeSchema(Schema):
    title: str
    prompt: str
    requirements: List[str] = []
    starter_template: str

class ChapterSummarySchema(Schema):
    order: int
    slug: str
    title: str
    category: str
    read_time: str
    takeaway: str
    seo_description: str
    videos_count: int = 0
    quizzes_count: int = 0
    challenges_count: int = 0

class ChapterDetailSchema(Schema):
    order: int
    slug: str
    title: str
    category: str
    read_time: str
    takeaway: str
    seo_description: str
    introduction: str
    analogy: Optional[AnalogySchema] = None
    mental_model: Optional[str] = None
    why_exists: Optional[str] = None
    use_case: Optional[Dict[str, Any]] = None
    syntax_guide: Optional[str] = None
    first_example: Optional[Dict[str, Any]] = None
    how_it_works: Optional[str] = None
    starter_code: str
    progressive_examples: List[ProgressiveExampleSchema] = []
    video_tutorials: List[VideoTutorialSchema] = []
    common_mistakes: List[CommonMistakeSchema] = []
    rules: List[RuleSchema] = []
    comparison: Optional[ComparisonSchema] = None
    performance: Optional[str] = None
    mini_project: Optional[MiniProjectSchema] = None
    practice_exercises: List[PracticeExerciseSchema] = []
    predict_quizzes: List[PredictQuizSchema] = []
    debug_challenges: List[DebugChallengeSchema] = []
    interview_questions: List[InterviewQuestionSchema] = []
    quick_revision: List[str] = []
    final_challenge: Optional[FinalChallengeSchema] = None
    prev_chapter: Optional[Dict[str, str]] = None
    next_chapter: Optional[Dict[str, str]] = None

# Interactive Execution & Quiz Schemas
class QuizSubmitRequest(Schema):
    chapter_slug: str
    quiz_index: int
    selected_option: str

class QuizSubmitResponse(Schema):
    is_correct: bool
    selected_option: str
    correct_answer: str
    explanation: str

class CodeExecuteRequest(Schema):
    code: str
    language: str = "javascript"

class CodeTraceStepSchema(Schema):
    step: int
    line_number: int
    event: str
    func_name: Optional[str] = None
    call_stack: List[str] = []
    variables: Dict[str, Any] = {}
    stdout_buffer: Optional[str] = ""
    heap_objects: Dict[str, Any] = {}
    explanation: Optional[str] = ""

class CodeExecuteResponse(Schema):
    success: bool
    total_steps: int
    execution_time_ms: float
    output: str
    steps: List[CodeTraceStepSchema] = []
    error: Optional[str] = None

class RoadmapStageSchema(Schema):
    stage_number: int
    stage_title: str
    badge_color: str
    description: str
    chapters: List[ChapterSummarySchema]

class CurriculumOverviewSchema(Schema):
    total_javascript_chapters: int
    total_python_chapters: int
    total_java_chapters: int
    total_sql_datasets: int
    total_practice_quizzes: int
    total_debug_challenges: int
    total_video_tutorials: int
    categories: List[str]
