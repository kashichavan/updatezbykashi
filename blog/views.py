from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.core.paginator import Paginator
from .models import BlogPost, Category, Tag

def blog_list_view(request):
    """
    Renders modern technical blog directory with category filtering, search, and featured carousel.
    """
    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('q', '').strip()

    posts_qs = BlogPost.objects.filter(is_published=True).select_related('category').prefetch_related('tags')

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        posts_qs = posts_qs.filter(category=active_category)

    active_tag = None
    if tag_slug:
        active_tag = get_object_or_404(Tag, slug=tag_slug)
        posts_qs = posts_qs.filter(tags=active_tag)

    if search_query:
        posts_qs = posts_qs.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # Featured posts for hero
    featured_posts = BlogPost.objects.filter(is_published=True, is_featured=True).select_related('category')[:3]

    # Categories with published count
    categories = Category.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__is_published=True))
    ).order_by('order', 'name')

    # Popular tags
    popular_tags = Tag.objects.annotate(
        posts_count=Count('posts', filter=Q(posts__is_published=True))
    ).filter(posts_count__gt=0).order_by('-posts_count')[:15]

    # Pagination
    paginator = Paginator(posts_qs, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': page_obj,
        'featured_posts': featured_posts,
        'categories': categories,
        'popular_tags': popular_tags,
        'active_category': active_category,
        'active_tag': active_tag,
        'search_query': search_query,
        'total_posts_count': BlogPost.objects.filter(is_published=True).count(),
        'meta_title': "Engineering Blog & Tech Deep Dives — Kashii Updatez",
        'meta_description': "In-depth engineering articles on V8 engine internals, JavaScript ES6+, React 19, Next.js architecture, Django Ninja, and PostgreSQL query optimization."
    }
    return render(request, 'blog/index.html', context)


def blog_detail_view(request, slug):
    """
    Renders rich technical article with Markdown/HTML rendering, reading progress bar, table of contents, and related posts.
    """
    post = get_object_or_404(
        BlogPost.objects.select_related('category').prefetch_related('tags'),
        slug=slug,
        is_published=True
    )

    # Increment view count
    BlogPost.objects.filter(pk=post.pk).update(views_count=post.views_count + 1)

    # Fetch 3 related posts
    related_posts = (
        BlogPost.objects.filter(is_published=True, category=post.category)
        .exclude(pk=post.pk)
        .select_related('category')[:3]
    )

    context = {
        'post': post,
        'related_posts': related_posts,
        'meta_title': f"{post.title} — Kashii Engineering Blog",
        'meta_description': post.seo_description or post.excerpt,
    }
    return render(request, 'blog/detail.html', context)


from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def blog_create_view(request):
    """
    Renders live Studio Editor to create, preview, and publish technical articles.
    """
    if request.method == 'POST':
        # Check authentication (or superuser / staff)
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, "⚠️ You must be logged in as an Admin / Staff to publish articles.")
            return redirect(f"/admin/login/?next=/blog/manage/new/")

        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '').strip()
        category_id = request.POST.get('category')
        tags_str = request.POST.get('tags', '').strip()
        cover_image_url = request.POST.get('cover_image_url', '').strip()
        author_name = request.POST.get('author_name', 'Kashinath Chavan').strip()
        author_title = request.POST.get('author_title', 'Founder & Software Architect').strip()
        author_avatar = request.POST.get('author_avatar_url', '').strip()
        is_published = request.POST.get('is_published') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        if not title or not content:
            messages.error(request, "Title and Content are required fields.")
            categories = Category.objects.all()
            return render(request, 'blog/create.html', {'categories': categories})

        category = Category.objects.filter(pk=category_id).first() if category_id else None

        post = BlogPost(
            title=title,
            slug=slug,
            excerpt=excerpt or title,
            content=content,
            category=category,
            cover_image_url=cover_image_url or "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=1200",
            author_name=author_name,
            author_title=author_title,
            author_avatar_url=author_avatar or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
            is_published=is_published,
            is_featured=is_featured,
        )
        post.save()

        # Process Tags
        if tags_str:
            tag_names = [t.strip().lstrip('#') for t in tags_str.split(',') if t.strip()]
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                post.tags.add(tag)

        messages.success(request, f"✨ Article '{post.title}' successfully created!")
        return redirect('blog:blog_detail', slug=post.slug)

    categories = Category.objects.all()
    all_tags = Tag.objects.all()
    context = {
        'categories': categories,
        'all_tags': all_tags,
        'meta_title': "Create New Article — Kashii Blog Studio",
        'meta_description': "Publish technical articles, V8 deep dives, and tutorials."
    }
    return render(request, 'blog/create.html', context)


def api_blog_like_view(request, slug):
    """AJAX endpoint for Medium-style claps/likes."""
    if request.method == 'POST':
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        BlogPost.objects.filter(pk=post.pk).update(likes_count=post.likes_count + 1)
        post.refresh_from_db()
        return JsonResponse({'success': True, 'likes_count': post.likes_count})
    return JsonResponse({'error': 'POST required'}, status=405)

