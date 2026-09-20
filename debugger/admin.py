from django.contrib import admin
from .models import CodeSnippet, DebugSession

@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('title', 'code')

@admin.register(DebugSession)
class DebugSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'language', 'total_steps', 'created_at')
    list_filter = ('language', 'created_at')
