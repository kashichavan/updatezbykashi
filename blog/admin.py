from django.contrib import admin
from django.utils.html import format_html
from .models import BlogPost, Category, Tag

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_with_icon', 'slug', 'color_badge', 'order', 'post_count', 'created_at')
    list_editable = ('order',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    def name_with_icon(self, obj):
        return f"{obj.icon} {obj.name}"
    name_with_icon.short_description = "Category"

    def color_badge(self, obj):
        return format_html(
            '<span style="background-color:{}; color:#fff; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:11px;">{}</span>',
            obj.color or '#38bdf8',
            obj.color
        )
    color_badge.short_description = "Color"

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = "Posts"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = "Tagged Posts"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title_preview',
        'category_badge',
        'author_name',
        'read_time_badge',
        'views_count',
        'is_published_badge',
        'is_featured_badge',
        'published_at',
        'live_preview_link'
    )
    list_filter = ('is_published', 'is_featured', 'category', 'tags', 'published_at')
    search_fields = ('title', 'excerpt', 'content', 'author_name', 'seo_title')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('views_count', 'likes_count', 'created_at', 'updated_at')
    actions = ['publish_posts', 'unpublish_posts', 'feature_posts', 'unfeature_posts']
    date_hierarchy = 'published_at'

    fieldsets = (
        ('📝 Article Overview & Core Content', {
            'fields': (
                'title',
                'slug',
                'category',
                'excerpt',
                'content',
            ),
            'description': 'Write and structure the technical article. You can use Markdown or clean HTML formatting.'
        }),
        ('🎨 Author & Media Assets', {
            'fields': (
                'cover_image_url',
                'author_name',
                'author_title',
                'author_avatar_url',
            ),
            'classes': ('collapse',),
        }),
        ('🚀 Publishing & Taxonomy', {
            'fields': (
                'is_published',
                'is_featured',
                'published_at',
                'read_time_minutes',
                'tags',
            )
        }),
        ('🔍 SEO & Metadata', {
            'fields': (
                'seo_title',
                'seo_description',
                'canonical_url',
            ),
            'classes': ('collapse',),
        }),
        ('📊 Engagement Metrics (Auto-tracked)', {
            'fields': (
                'views_count',
                'likes_count',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def title_preview(self, obj):
        return obj.title[:65] + ('...' if len(obj.title) > 65 else '')
    title_preview.short_description = "Title"

    def category_badge(self, obj):
        if not obj.category:
            return "-"
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; border-radius:4px; font-weight:700; font-size:11px;">{} {}</span>',
            obj.category.color or '#0284c7',
            obj.category.icon,
            obj.category.name
        )
    category_badge.short_description = "Category"

    def read_time_badge(self, obj):
        return f"⏱️ {obj.read_time_minutes} min"
    read_time_badge.short_description = "Read Time"

    def is_published_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color:#10b981; font-weight:bold;">● Published</span>')
        return format_html('<span style="color:#ef4444; font-weight:bold;">○ Draft</span>')
    is_published_badge.short_description = "Status"

    def is_featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="background:#f59e0b; color:#000; padding:1px 6px; border-radius:4px; font-weight:800; font-size:10px;">⭐ FEATURED</span>')
        return "-"
    is_featured_badge.short_description = "Featured"

    def live_preview_link(self, obj):
        if obj.is_published:
            return format_html('<a href="/blog/{}/" target="_blank" style="color:#38bdf8; font-weight:bold;">👁️ View Live</a>', obj.slug)
        return format_html('<a href="/blog/{}/" target="_blank" style="color:#94a3b8;">Preview</a>', obj.slug)
    live_preview_link.short_description = "Live Link"

    # Admin Actions
    @admin.action(description="✅ Publish selected blog posts")
    def publish_posts(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f"Successfully published {count} blog post(s).")

    @admin.action(description="🚫 Unpublish (convert to Draft)")
    def unpublish_posts(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f"Successfully converted {count} blog post(s) to draft.")

    @admin.action(description="⭐ Mark as Featured for Hero Carousel")
    def feature_posts(self, request, queryset):
        count = queryset.update(is_featured=True)
        self.message_user(request, f"Marked {count} post(s) as featured.")

    @admin.action(description="Remove Featured status")
    def unfeature_posts(self, request, queryset):
        count = queryset.update(is_featured=False)
        self.message_user(request, f"Removed featured status from {count} post(s).")
