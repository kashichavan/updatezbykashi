import {
  BlogPost,
  BlogPostsResponse,
  Category,
  Tag,
  ChapterSummary,
  ChapterDetail,
  CodeExecuteResponse,
  RoadmapStage,
  OwnerJob,
  OwnerJobsResponse,
  OwnerGroup,
  OwnerGroupsResponse,
  BulletPolishRequest,
  BulletPolishResponse,
  ResumeTailorRequest,
  ResumeTailorResponse,
  SummaryGenRequest,
  SummaryGenResponse,
  JobDescriptionRequest,
  JobDescriptionResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

// API cache helper
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 60_000; // 1 minute

function cachedFetch<T>(key: string, url: string | RequestInfo, init?: RequestInit): Promise<T> {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return Promise.resolve(cached.data as T);
  }
  return fetch(url, init).then(async (res) => {
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    const data = (await res.json()) as T;
    cache.set(key, { data, timestamp: Date.now() });
    return data;
  });
}

// ── 1. BLOG API METHODS ──
export async function getBlogPosts(params?: {
  category?: string;
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<BlogPostsResponse> {
  const query = new URLSearchParams();
  if (params?.category) query.set('category', params.category);
  if (params?.tag) query.set('tag', params.tag);
  if (params?.search) query.set('search', params.search);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  const res = await fetch(`${API_BASE_URL}/blog/posts?${query.toString()}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) throw new Error('Failed to fetch blog posts from Django Ninja API');
  return res.json();
}

export async function getBlogPostBySlug(slug: string): Promise<BlogPost | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/blog/posts/${slug}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getBlogCategories(): Promise<Category[]> {
  const res = await fetch(`${API_BASE_URL}/blog/categories`, {
    next: { revalidate: 120 },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getFeaturedPosts(limit: number = 3): Promise<BlogPost[]> {
  const res = await fetch(`${API_BASE_URL}/blog/featured?limit=${limit}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return [];
  return res.json();
}


// ── 2. JAVASCRIPT MASTERCLASS CURRICULUM API METHODS ──
export async function getJavaScriptChapters(category?: string): Promise<ChapterSummary[]> {
  const query = category ? `?category=${encodeURIComponent(category)}` : '';
  const res = await fetch(`${API_BASE_URL}/curriculum/javascript/chapters${query}`, {
    next: { revalidate: 120 },
  });
  if (!res.ok) throw new Error('Failed to fetch JavaScript curriculum chapters');
  return res.json();
}

export async function getJavaScriptChapterDetail(slug: string): Promise<ChapterDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/curriculum/javascript/chapters/${slug}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function getJavaScriptRoadmap(): Promise<RoadmapStage[]> {
  const res = await fetch(`${API_BASE_URL}/curriculum/javascript/roadmap`, {
    next: { revalidate: 300 },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function executeJavaScriptCode(code: string): Promise<CodeExecuteResponse> {
  const res = await fetch(`${API_BASE_URL}/curriculum/javascript/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    // Attempt to parse JSON error from backend
    const errorBody = await res.json().catch(() => ({ detail: 'API Execution Failed' }));
    return {
      success: false,
      total_steps: 0,
      execution_time_ms: 0,
      output: '',
      steps: [],
      error: errorBody.detail || 'API Execution Failed',
    };
  }
  return res.json();
}

export async function submitQuizAnswer(
  chapterSlug: string,
  quizIndex: number,
  selectedOption: string,
): Promise<{ is_correct: boolean; correct_answer: string; explanation: string }> {
  const res = await fetch(`${API_BASE_URL}/curriculum/javascript/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chapter_slug: chapterSlug,
      quiz_index: quizIndex,
      selected_option: selectedOption,
    }),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to submit quiz answer' }));
    throw new Error(errorBody.detail || 'Failed to submit quiz answer');
  }
  return res.json();
}

// ── 3. OWNER DASHBOARD API FETCH METHODS ──
export async function getOwnerJobs(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  experience?: 'ALL' | 'FRESHER' | 'EXPERIENCED' | 'INTERNSHIP';
  status?: string;
  sort?: string;
}): Promise<OwnerJobsResponse> {
  const query = new URLSearchParams();
  if (params?.page) query.set('page', String(params.page));
  if (params?.page_size) query.set('page_size', String(params.page_size));
  if (params?.search) query.set('search', params.search);
  if (params?.category) query.set('category', params.category);
  if (params?.experience && params.experience !== 'ALL') query.set('experience', params.experience);
  if (params?.status) query.set('status', params.status);
  if (params?.sort) query.set('sort', params.sort);

  return cachedFetch<OwnerJobsResponse>(
    `owner_jobs_${query.toString()}`,
    `${API_BASE_URL}/owner/jobs/?${query.toString()}`,
    { next: { revalidate: 60 } } as any
  );
}

export async function getOwnerGroups(params?: {
  page?: number;
  page_size?: number;
  tier_type?: 'ALL' | 'FRESHER' | 'EXPERIENCED' | 'GENERAL';
}): Promise<OwnerGroupsResponse> {
  const query = new URLSearchParams();
  if (params?.page) query.set('page', String(params.page));
  if (params?.page_size) query.set('page_size', String(params.page_size));
  if (params?.tier_type && params.tier_type !== 'ALL') query.set('tier_type', params.tier_type);

  return cachedFetch<OwnerGroupsResponse>(
    `owner_groups_${query.toString()}`,
    `${API_BASE_URL}/owner/groups/?${query.toString()}`,
    { next: { revalidate: 60 } } as any
  );
}

export async function autoOrganizeGroups(): Promise<{
  status: string;
  message: string;
  groups_created: number;
  jobs_organized: number;
}> {
  const res = await fetch(`${API_BASE_URL}/owner/groups/auto-organize/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to auto-organize groups' }));
    throw new Error(errorBody.detail || 'Failed to auto-organize groups');
  }
  return res.json();
}

// ── 4. AI CAREER & JOB TOOLS API METHODS ──
export async function api_polish_bullet(payload: BulletPolishRequest): Promise<BulletPolishResponse> {
  const res = await fetch(`${API_BASE_URL}/ai/polish-bullet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to polish bullet point' }));
    throw new Error(errorBody.detail || 'Failed to polish bullet point');
  }
  return res.json();
}

export async function api_tailor_resume(payload: ResumeTailorRequest): Promise<ResumeTailorResponse> {
  const res = await fetch(`${API_BASE_URL}/ai/tailor-resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to tailor resume' }));
    throw new Error(errorBody.detail || 'Failed to tailor resume');
  }
  return res.json();
}

export async function api_generate_jd(payload: JobDescriptionRequest): Promise<JobDescriptionResponse> {
  const res = await fetch(`${API_BASE_URL}/ai/generate-jd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to generate job description' }));
    throw new Error(errorBody.detail || 'Failed to generate job description');
  }
  return res.json();
}

export async function api_generate_summary(payload: SummaryGenRequest): Promise<SummaryGenResponse> {
  const res = await fetch(`${API_BASE_URL}/ai/generate-summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ detail: 'Failed to generate summary' }));
    throw new Error(errorBody.detail || 'Failed to generate summary');
  }
  return res.json();
}
