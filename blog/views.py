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
