// ── BLOG INTERFACES ──
export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  order: number;
  posts_count?: number;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
  posts_count?: number;
}

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover_image_url?: string | null;
  author_name: string;
  author_title: string;
  author_avatar_url?: string | null;
  category?: Category | null;
  tags: Tag[];
  read_time_minutes: number;
  views_count: number;
  likes_count: number;
  is_featured: boolean;
  published_at: string;
  content?: string;
  seo_title?: string;
  seo_description?: string;
  related_posts?: BlogPost[];
}

export interface BlogPostsResponse {
  total: number;
  limit: number;
  offset: number;
  posts: BlogPost[];
}

// ── JAVASCRIPT MASTERCLASS INTERFACES ──
export interface ProgressiveExample {
  tier: string;
  title: string;
  description: string;
  code: string;
  output?: string;
  notes?: string;
}

export interface VideoTutorial {
  title: string;
  channel: string;
  youtube_id: string;
  duration: string;
  level: string;
  description: string;
}

export interface CommonMistake {
  title: string;
  bad: string;
  why_bad: string;
  good: string;
  why_good: string;
}

export interface Rule {
  rule: string;
  detail: string;
}

export interface ComparisonRow {
  feature: string;
  val_a: string;
  val_b: string;
}

export interface Comparison {
  title: string;
  item_a: string;
  item_b: string;
  rows: ComparisonRow[];
}

export interface PracticeExercise {
  level: string;
  title: string;
  prompt: string;
  hint: string;
  solution: string;
}

export interface PredictQuiz {
  code: string;
  options: string[];
  answer: string;
  explanation: string;
}

export interface DebugChallenge {
  context: string;
  broken_code: string;
  bug_reason: string;
  fixed_code: string;
}

export interface InterviewQuestion {
  tier: string;
  question: string;
  answer: string;
}

export interface ChapterSummary {
  order: number;
  slug: string;
  title: string;
  category: string;
  read_time: string;
  takeaway: string;
  seo_description: string;
  videos_count: number;
  quizzes_count: number;
  challenges_count: number;
}

export interface ChapterDetail extends ChapterSummary {
  introduction: string;
  analogy?: {
    title: string;
    text: string;
    mapping: Array<{ real: string; prog: string }>;
  };
  mental_model?: string;
  why_exists?: string;
  use_case?: { company: string; text: string };
  syntax_guide?: string;
  first_example?: { title: string; code: string; output: string; explanation: string };
  how_it_works?: string;
  starter_code: string;
  progressive_examples: ProgressiveExample[];
  video_tutorials: VideoTutorial[];
  common_mistakes: CommonMistake[];
  rules: Rule[];
  comparison?: Comparison;
  performance?: string;
  mini_project?: {
    title: string;
    problem: string;
    requirements: string[];
    solution_code: string;
    solution_explanation: string;
  };
  practice_exercises: PracticeExercise[];
  predict_quizzes: PredictQuiz[];
  debug_challenges: DebugChallenge[];
  interview_questions: InterviewQuestion[];
  quick_revision: string[];
  final_challenge?: {
    title: string;
    prompt: string;
    requirements: string[];
    starter_template: string;
  };
  prev_chapter?: { slug: string; title: string } | null;
  next_chapter?: { slug: string; title: string } | null;
}

export interface CodeTraceStep {
  step: number;
  line_number: number;
  event: string;
  func_name?: string;
  call_stack: string[];
  variables: Record<string, any>;
  stdout_buffer?: string;
  explanation?: string;
}

export interface CodeExecuteResponse {
  success: boolean;
  total_steps: number;
  execution_time_ms: number;
  output: string;
  steps: CodeTraceStep[];
  error?: string | null;
}

export interface QuizSubmitRequest {
  chapter_slug: string;
  quiz_index: number;
  selected_option: string;
}

export interface QuizSubmitResponse {
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
}

// ── OWNER DASHBOARD INTERFACES ──
export interface OwnerJob {
  id: number;
  title: string;
  company_name: string;
  company_logo?: string | null;
  location: string;
  domain: string;
  source: string;
  job_type: string;
  experience_tier: string;
  category: string;
  status: string;
  posted_date: string;
  deadline: string;
  description?: string;
  requirements?: string[];
  skills?: string[];
}

export interface OwnerJobsResponse {
  jobs: OwnerJob[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OwnerGroup {
  id: number;
  name: string;
  slug: string;
  banner_tag: string;
  description: string;
  tier_type: string;
  jobs: OwnerJob[];
}

export interface OwnerGroupsResponse {
  groups: OwnerGroup[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RoadmapStage {
  stage_number: number;
  stage_title: string;
  badge_color: string;
  description: string;
  chapters: ChapterSummary[];
}

// ── AI CAREER & JOB TOOLS INTERFACES ──
export interface JobDescriptionRequest {
  title: string;
  company?: string;
  experience?: string;
  location?: string;
  work_mode?: string;
  skills?: string;
  additional_notes?: string;
}

export interface JobDescriptionResponse {
  success: boolean;
  data?: any;
  error?: string;
}

export interface BulletPolishRequest {
  bullet: string;
  role?: string;
  tech_stack?: string;
}

export interface BulletPolishResponse {
  success: boolean;
  data?: string;
  error?: string;
}

export interface ResumeTailorRequest {
  resume_summary: string;
  resume_skills: string[];
  resume_projects: { title: string; bullets: string }[];
  job_description: string;
}

export interface ResumeTailorResponse {
  success: boolean;
  data?: string;
  error?: string;
}

export interface SummaryGenRequest {
  role: string;
  experience_level?: string;
  key_skills?: string;
  target_company_type?: string;
}

export interface SummaryGenResponse {
  success: boolean;
  data?: string;
  error?: string;
}
