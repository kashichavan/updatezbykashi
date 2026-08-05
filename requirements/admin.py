from django.contrib import admin
from .models import Category, JobPosting, StudentApplication

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'posted_date', 'job_type', 'stipend_salary', 'location', 'deadline', 'status', 'is_featured')
    list_filter = ('job_type', 'status', 'is_remote', 'category', 'is_featured', 'posted_date')
    search_fields = ('title', 'company_name', 'skills_required', 'description')
    ordering = ('-posted_date', '-created_at')
    date_hierarchy = 'posted_date'
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'student_email', 'job', 'degree_major', 'graduation_year', 'status', 'applied_at')
    list_filter = ('status', 'graduation_year')
    search_fields = ('student_name', 'student_email', 'job__title')
    ordering = ('-applied_at',)
