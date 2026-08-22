from ninja import Router, Query
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from typing import List, Optional
from blog.models import BlogPost, Category, Tag
from api.schemas import (
    BlogPostListSchema,
    BlogPostDetailSchema,
    BlogPostsResponse,
    CategorySchema,
    TagSchema
)

router = Router(tags=["Blog & Technical Articles"])

@router.get("/posts", response=BlogPostsResponse, summary="List published blog posts")
def list_posts(
    request,
    category: Optional[str] = Query(None, description="Filter by category slug"),
    tag: Optional[str] = Query(None, description="Filter by tag slug"),
    search: Optional[str] = Query(None, description="Search across title, excerpt, content"),
    is_featured: Optional[bool] = Query(None, description="Filter featured posts"),
    limit: int = Query(10, ge=1, le=50, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Fetch a paginated list of published technical blog posts with optional category, tag, or keyword search.
    """
    qs = BlogPost.objects.filter(is_published=True).select_related('category').prefetch_related('tags')

    if category:
        qs = qs.filter(category__slug=category)
    if tag:
        qs = qs.filter(tags__slug=tag)
    if is_featured is not None:
        qs = qs.filter(is_featured=is_featured)
    if search:
        search = search.strip()
        qs = qs.filter(
            Q(title__icontains=search) |
            Q(excerpt__icontains=search) |
            Q(content__icontains=search)
        )

    total = qs.count()
    posts = list(qs[offset:offset + limit])
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "posts": posts
    }

@router.get("/posts/{slug}", response=BlogPostDetailSchema, summary="Get full blog post by slug")
def get_post_detail(request, slug: str):
    """
    Fetch complete blog article content, SEO metadata, reading time, and 3 related posts in the same category.
    """
    post = get_object_or_404(
        BlogPost.objects.select_related('category').prefetch_related('tags'),
        slug=slug,
        is_published=True
    )
    
    # Increment view count in a light non-blocking way
    BlogPost.objects.filter(pk=post.pk).update(views_count=post.views_count + 1)
    
    # Fetch up to 3 related posts
    related = list(
        BlogPost.objects.filter(is_published=True, category=post.category)
        .exclude(pk=post.pk)
        .select_related('category')
        .prefetch_related('tags')[:3]
    )
    
    # Attach related_posts to output object
    post.related_posts = related
    return post

@router.get("/categories", response=List[CategorySchema], summary="List categories with post counts")
def list_categories(request):
    """
    Fetch all active blog categories with their published post count.
    """
    categories = (
        Category.objects.annotate(
            posts_count=Count('posts', filter=Q(posts__is_published=True))
        )
        .order_by('order', 'name')
    )
    return list(categories)

@router.get("/tags", response=List[TagSchema], summary="List popular tags")
def list_tags(request):
    """
    Fetch all tags with active post counts.
    """
    tags = (
        Tag.objects.annotate(
            posts_count=Count('posts', filter=Q(posts__is_published=True))
        )
        .filter(posts_count__gt=0)
        .order_by('-posts_count', 'name')[:30]
    )
    return list(tags)

@router.get("/featured", response=List[BlogPostListSchema], summary="Get featured blog hero posts")
def get_featured_posts(request, limit: int = 3):
    """
    Fetch highlighted featured articles for the blog hero carousel.
    """
    posts = list(
        BlogPost.objects.filter(is_published=True, is_featured=True)
        .select_related('category')
        .prefetch_related('tags')[:limit]
    )
    if not posts:
        posts = list(
            BlogPost.objects.filter(is_published=True)
            .select_related('category')
            .prefetch_related('tags')[:limit]
        )
    return posts

from api.schemas import BlogPostCreateSchema

@router.post("/posts", response=BlogPostDetailSchema, summary="Create a new blog post via API")
def create_blog_post(request, payload: BlogPostCreateSchema):
    """
    Create a new technical blog post programmatically.
    """
    cat = None
    if payload.category_id:
        cat = Category.objects.filter(pk=payload.category_id).first()

    post = BlogPost(
        title=payload.title,
        slug=payload.slug or "",
        excerpt=payload.excerpt,
        content=payload.content,
        category=cat,
        cover_image_url=payload.cover_image_url,
        author_name=payload.author_name or "Kashinath Chavan",
        author_title=payload.author_title or "Founder & Software Architect",
        author_avatar_url=payload.author_avatar_url,
        is_published=payload.is_published if payload.is_published is not None else True,
        is_featured=payload.is_featured if payload.is_featured is not None else False,
        seo_title=payload.seo_title or "",
        seo_description=payload.seo_description or "",
    )
    post.save()

    if payload.tags:
        for tag_name in payload.tags:
            tag_clean = tag_name.strip().lstrip('#')
            if tag_clean:
                t, _ = Tag.objects.get_or_create(name=tag_clean)
                post.tags.add(t)

    post.related_posts = []
    return post
