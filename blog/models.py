from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import math
import re

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, default='📄', help_text="Emoji or Icon identifier")
    color = models.CharField(max_length=30, default='#38bdf8', help_text="Hex color code")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt = models.TextField(help_text="Short summary for cards and search snippets (150-250 chars)")
    content = models.TextField(help_text="Full post content in Markdown or HTML")
    
    # Media & Author
    cover_image_url = models.URLField(max_length=500, blank=True, null=True)
    author_name = models.CharField(max_length=100, default="Kashinath Chavan")
    author_title = models.CharField(max_length=150, default="Founder & Full-Stack Architect")
    author_avatar_url = models.URLField(max_length=500, blank=True, null=True, default="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150")
    
    # Classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    
    # Metrics
    read_time_minutes = models.PositiveIntegerField(default=5)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    
    # Status & Dates
    is_published = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO
    seo_title = models.CharField(max_length=150, blank=True, default='')
    seo_description = models.CharField(max_length=255, blank=True, default='')
    canonical_url = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at', 'is_published']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Calculate approximate read time
        words = len(re.findall(r'\w+', self.content or ''))
        if words > 0:
            self.read_time_minutes = max(1, math.ceil(words / 200))
            
        if not self.seo_title:
            self.seo_title = self.title[:140]
        if not self.seo_description and self.excerpt:
            self.seo_description = self.excerpt[:250]
            
        super().save(*args, **kwargs)
