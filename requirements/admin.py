from django.contrib import admin
from django.utils.html import format_html
from .models import Category, JobPosting, StudentApplication, ContactInquiry

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company_name',
        'posted_date',
        'job_type',
        'stipend_salary',
        'location',
        'status',
        'story_direct_links',
        'is_featured',
    )
    list_filter = ('job_type', 'status', 'is_remote', 'category', 'is_featured', 'posted_date', 'insta_story_published')
    search_fields = ('title', 'company_name', 'skills_required', 'description')
    ordering = ('-posted_date', '-created_at')
    date_hierarchy = 'posted_date'
    readonly_fields = ('created_at', 'updated_at', 'story_preview_card', 'story_metadata_card')

    fieldsets = (
        ('Lead Information', {
            'fields': ('title', 'company_name', 'company_logo_icon', 'category', 'job_type', 'experience_tier', 'stipend_salary', 'location', 'normalized_city', 'is_remote')
        }),
        ('Instagram Story Assets', {
            'description': 'Direct links to 9:16 Instagram Story image, caption, and link sticker target for Instagram & ReelFlow.',
            'fields': ('story_preview_card', 'story_metadata_card', 'insta_story_published', 'insta_story_media_id', 'insta_story_published_at')
        }),
        ('Application & Description', {
            'fields': ('apply_url', 'allow_direct_apply', 'description', 'eligibility', 'skills_required', 'selection_process', 'contact_phone')
        }),
        ('Lifecycle & Expiration', {
            'fields': ('status', 'deadline', 'is_featured', 'posted_date', 'created_at', 'updated_at')
        }),
    )

    def story_direct_links(self, obj):
        if not obj or not obj.id:
            return "-"
        image_url = obj.get_story_image_url()
        sticker_url = obj.get_story_sticker_url()
        published = obj.insta_story_published
        badge_color = "#10b981" if published else "#f59e0b"
        badge_text = "Published" if published else "Ready"
        return format_html(
            '<div style="display:inline-flex;gap:5px;align-items:center;flex-wrap:wrap;">'
            '<a href="{}" target="_blank" style="padding:3px 8px;font-size:11px;font-weight:700;background:#2563eb;color:#ffffff;border-radius:4px;text-decoration:none;" title="Open 9:16 Story Image directly">📸 9:16 Image ↗</a>'
            '<a href="{}" target="_blank" style="padding:3px 8px;font-size:11px;font-weight:700;background:#0f172a;color:#ffffff;border-radius:4px;text-decoration:none;" title="Direct Link for IG Link Sticker">🔗 Sticker Link ↗</a>'
            '<span style="padding:2px 6px;border-radius:99px;font-size:10px;font-weight:800;background:{};color:#fff;">{}</span>'
            '</div>',
            image_url,
            sticker_url,
            badge_color,
            badge_text
        )
    story_direct_links.short_description = "Instagram Story"

    def story_preview_card(self, obj):
        if not obj or not obj.id:
            return "Save job requirement first to generate Instagram Story."
        image_url = obj.get_story_image_url()
        return format_html(
            '<div style="max-width:280px;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.18);border:1px solid #cbd5e1;">'
            '<a href="{}" target="_blank" title="Click to view full 1080x1920 image">'
            '<img src="{}" style="width:100%;height:auto;display:block;" alt="9:16 Instagram Story Preview">'
            '</a>'
            '</div>',
            image_url,
            image_url
        )
    story_preview_card.short_description = "9:16 Story Preview"

    def story_metadata_card(self, obj):
        if not obj or not obj.id:
            return "-"
        image_url = obj.get_story_image_url()
        sticker_url = obj.get_story_sticker_url()
        caption = obj.get_insta_story_text(share_url=sticker_url)
        return format_html(
            '<div style="line-height:1.7;font-size:13px;">'
            '<div><strong>📸 Direct 9:16 Story Image:</strong> <a href="{}" target="_blank">{}</a></div>'
            '<div><strong>🔗 Direct Link Sticker URL:</strong> <a href="{}" target="_blank">{}</a></div>'
            '<div><strong>⚡ Instagram Automation App:</strong> <a href="https://insta.kashiiupdatez.online" target="_blank" style="font-weight:700;color:#e1306c;">insta.kashiiupdatez.online ↗</a></div>'
            '<div style="margin-top:10px;"><strong>📋 Formatted Instagram Story Caption (Ready to Paste):</strong>'
            '<pre style="background:#f8fafc;border:1px solid #cbd5e1;padding:10px;border-radius:8px;max-height:160px;overflow-y:auto;white-space:pre-wrap;font-family:monospace;font-size:12px;color:#0f172a;">{}</pre>'
            '</div>'
            '</div>',
            image_url, image_url,
            sticker_url, sticker_url,
            caption
        )
    story_metadata_card.short_description = "Story Assets & Direct Links"

@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'student_email', 'job', 'degree_major', 'graduation_year', 'status', 'applied_at')
    list_filter = ('status', 'graduation_year')
    search_fields = ('student_name', 'student_email', 'job__title')
    ordering = ('-applied_at',)


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    ordering = ('-created_at',)

