import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CodeSnippet(models.Model):
    """Stores user code programs and practice templates."""
    LANGUAGE_CHOICES = [
        ('python', 'Python 3'),
        ('javascript', 'JavaScript (Node.js/V8)'),
        ('java', 'Java 17'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="Untitled Program")
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    code = models.TextField(help_text="Source code for execution and debugging")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_language_display()})"


class DebugSession(models.Model):
    """Stores an active debugging session, breakpoints, and execution state history."""
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snippet = models.ForeignKey(CodeSnippet, on_delete=models.CASCADE, related_name='debug_sessions', null=True, blank=True)
    language = models.CharField(max_length=20, default='python')
    code = models.TextField()
    breakpoints = models.JSONField(default=list, help_text="List of line numbers set as breakpoints")
    total_steps = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"DebugSession {self.session_id} - {self.language} ({self.total_steps} steps)"


class ExecutionTraceStep(models.Model):
    """
    Stores an individual step in the program execution timeline.
    Captures exact line number, stack frames, variables state, heap objects, & stdout.
    """
    session = models.ForeignKey(DebugSession, on_delete=models.CASCADE, related_name='trace_steps')
    step_index = models.IntegerField(help_text="0-indexed step sequence in execution timeline")
    line_number = models.IntegerField(help_text="Currently executing line number in source code")
    line_text = models.CharField(max_length=512, blank=True)
    event_type = models.CharField(max_length=30, default='line', help_text="line, call, return, or exception")
    
    stack_frames = models.JSONField(default=list, help_text="Call stack representation [main() -> fn()]")
    variables = models.JSONField(default=dict, help_text="Variables state with types, values, & simulated memory pointers")
    heap_objects = models.JSONField(default=dict, help_text="Heap memory graph for lists, dicts, objects, & references")
    
    stdout = models.TextField(blank=True, help_text="Cumulative standard output stream at this step")
    ai_explanation = models.TextField(blank=True, help_text="Beginner-friendly explanation of what happened in this step")

    class Meta:
        ordering = ['step_index']
        unique_together = ('session', 'step_index')

    def __str__(self):
        return f"Step {self.step_index} [Line {self.line_number}]: {self.line_text[:30]}"
