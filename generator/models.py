from django.db import models
from django.utils import timezone
import uuid

class UserSession(models.Model):
    session_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    start_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    pages_visited = models.IntegerField(default=1)
    completion_status = models.CharField(
        max_length=20, 
        choices=[
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('partial', 'Partial'),
            ('abandoned', 'Abandoned')
        ],
        default='active'
    )
    referrer = models.URLField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_minutes(self):
        if self.completion_status in ['completed', 'abandoned']:
            return round((self.last_activity - self.start_time).total_seconds() / 60, 1)
        return round((timezone.now() - self.start_time).total_seconds() / 60, 1)

class PageView(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=200)
    method = models.CharField(max_length=10, default='GET')
    
    def __str__(self):
        return f"{self.path} - {self.timestamp.strftime('%H:%M:%S')}"

class PromptGeneration(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Form data
    template_used = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True)
    subject = models.TextField(blank=True)
    task = models.CharField(max_length=200, blank=True)
    context = models.CharField(max_length=100, blank=True)
    methodology = models.CharField(max_length=200, blank=True)
    tone = models.CharField(max_length=100, blank=True)
    generated_prompt = models.TextField(blank=True, null=True)  # Το actual prompt που δημιουργήθηκε
    
    # Process data
    enhancement_mode = models.CharField(
        max_length=20,
        choices=[('enhanced', 'Enhanced'), ('basic', 'Basic')],
        default='enhanced'
    )
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    response_time_seconds = models.FloatField(null=True, blank=True)
    
    # User actions
    copied_to_clipboard = models.BooleanField(default=False)
    improvement_requested = models.BooleanField(default=False)
    improvement_applied = models.BooleanField(default=False)
    
    def __str__(self):
        template_info = f"Template: {self.template_used}" if self.template_used else "No template"
        return f"{template_info} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class TemplateUsage(models.Model):
    template_name = models.CharField(max_length=100)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.template_name}: {self.usage_count} uses"
    
    class Meta:
        ordering = ['-usage_count']

class ImprovementSuggestion(models.Model):
    prompt_generation = models.ForeignKey(PromptGeneration, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    suggestion_text = models.TextField()
    applied = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Suggestion for {self.prompt_generation.id} - Applied: {self.applied}"