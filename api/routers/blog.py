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
    TagSchema,
    BlogPostCreateSchema # Import the creation schema
)
from api.auth import AuthBearer # Import our custom AuthBearer
from django.utils.text import slugify
from ninja.errors import HttpError

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

@router.post("/posts", response=BlogPostDetailSchema, auth=AuthBearer(), summary="Create a new blog post")
def create_post(request, payload: BlogPostCreateSchema):
    """
    Create a new blog post. Requires JWT authentication.
    The `author_name`, `author_title`, `author_avatar_url` will be automatically set from default values
    if not provided. The `slug` will be auto-generated from the title if not provided.
    """
    # Ensure user is authenticated and has permission (e.g., is_staff or custom permission)
    # For simplicity, assuming any authenticated user can create for now, but should be more granular
    if not request.auth: # request.auth will be the validated token if AuthBearer passes
        raise HttpError(401, "Unauthorized: Valid JWT token required.")
    
    # Generate slug if not provided
    if not payload.slug:
        payload.slug = slugify(payload.title)

    # Check for existing slug
    if BlogPost.objects.filter(slug=payload.slug).exists():
        raise HttpError(409, f"A blog post with slug '{payload.slug}' already exists.")

    # Handle category
    category_instance = None
    if payload.category_id:
        category_instance = get_object_or_404(Category, id=payload.category_id)

    post_data = payload.dict(exclude_unset=True)
    post_data['category'] = category_instance
    post_data.pop('tags', None) # Handle tags separately

    post = BlogPost.objects.create(**post_data)

    # Handle tags (create if not exists, then add)
    if payload.tags:
        for tag_name in payload.tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': slugify(tag_name)})
            post.tags.add(tag)

    return post


@router.put("/posts/{slug}", response=BlogPostDetailSchema, auth=AuthBearer(), summary="Update a blog post by slug")
def update_post(request, slug: str, payload: BlogPostCreateSchema):
    """
    Update an existing blog post by slug. Requires JWT authentication.
    Only fields provided in the payload will be updated.
    """
    if not request.auth:
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    post = get_object_or_404(BlogPost, slug=slug, is_published=True)

    # Prevent changing slug if it already exists and is different from new slug
    if payload.slug and payload.slug != slug and BlogPost.objects.filter(slug=payload.slug).exists():
        raise HttpError(409, f"A blog post with slug '{payload.slug}' already exists.")

    # Update fields from payload
    update_data = payload.dict(exclude_unset=True)

    if 'category_id' in update_data:
        category_instance = None
        if update_data['category_id']:
            category_instance = get_object_or_404(Category, id=update_data['category_id'])
        post.category = category_instance
        update_data.pop('category_id')

    if 'tags' in update_data:
        post.tags.clear()
        for tag_name in update_data['tags']:
            tag, _ = Tag.objects.get_or_create(name=tag_name, defaults={'slug': slugify(tag_name)})
            post.tags.add(tag)
        update_data.pop('tags')
    
    # Apply other updates
    for attr, value in update_data.items():
        setattr(post, attr, value)

    post.save() # This will also recalculate read_time_minutes and generate slug if empty
    return post

@router.delete("/posts/{slug}", summary="Delete a blog post by slug", auth=AuthBearer())
def delete_post(request, slug: str):
    """
    Delete an existing blog post by slug. Requires JWT authentication.
    """
    if not request.auth:
        raise HttpError(401, "Unauthorized: Valid JWT token required.")

    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    post.delete()
    return {"success": True, "message": f"Blog post '{slug}' deleted successfully.", "status_code": 204}


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
        .order_by('name')
    )
    return list(tags)

@router.get("/featured", response=List[BlogPostListSchema], summary="List featured blog posts")
def list_featured_posts(request, limit: int = Query(3, ge=1, le=10)):
    """
    Fetch a limited number of featured blog posts.
    """
    qs = BlogPost.objects.filter(is_published=True, is_featured=True)
    return list(qs[:limit])
