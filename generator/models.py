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

    # === NEW: ONBOARDING DEMOGRAPHICS ===
    ai_experience = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('none', 'No experience'),
            ('basic', 'Basic (e.g., ChatGPT)'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        help_text="User's self-reported AI tools experience level"
    )
    
    teaching_years = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ('0-5', '0-5 years'),
            ('6-15', '6-15 years'),
            ('16-25', '16-25 years'),
            ('25+', '25+ years'),
        ],
        help_text="Years of teaching experience"
    )
    
    onboarding_completed = models.BooleanField(default=False)
    onboarding_completion_time = models.DateTimeField(blank=True, null=True)
    onboarding_skipped = models.BooleanField(default=False)
    research_consent = models.BooleanField(default=True)
    contact_email = models.EmailField(blank=True, null=True)

    # === PHASE 2: TRAINING NEEDS SURVEY ===
    training_needs_completed = models.BooleanField(default=False)
    training_needs_completion_time = models.DateTimeField(blank=True, null=True)
    training_needs_shown = models.BooleanField(default=False)
    
    # Training interests (all selected areas)
    training_interests = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of all training areas the user is interested in"
    )
    
    # Top 3 priorities (ranked)
    training_priorities = models.JSONField(
        default=dict,
        blank=True, 
        help_text="Dictionary with priority rankings: {'area': priority_number}"
    )
    
    # Other training needs (free text)
    training_other_needs = models.TextField(blank=True, null=True)
    
    # Research participation
    follow_up_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Email for AI education research participation"
    )
    research_interview_interest = models.BooleanField(
        default=False,
        help_text="Interest in participating in research interview"
    )
    
    @property
    def duration_minutes(self):
        if self.completion_status in ['completed', 'abandoned']:
            return round((self.last_activity - self.start_time).total_seconds() / 60, 1)
        return round((timezone.now() - self.start_time).total_seconds() / 60, 1)
    
    @property
    def user_profile_summary(self):
        """Human-readable summary of user demographics"""
        if not self.ai_experience or not self.teaching_years:
            return "Profile incomplete"
        
        ai_exp = dict(self._meta.get_field('ai_experience').choices).get(self.ai_experience, self.ai_experience)
        teaching_exp = dict(self._meta.get_field('teaching_years').choices).get(self.teaching_years, self.teaching_years)
        
        return f"{ai_exp} AI user, {teaching_exp} teaching"
    
    @property
    def is_demographics_complete(self):
        """Check if basic demographics are collected"""
        return bool(self.ai_experience and self.teaching_years)
    
    @property
    def research_participant_type(self):
        """Categorize user for research purposes"""
        if not self.is_demographics_complete:
            return "Unknown"
        
        # Create research-relevant categories
        if self.ai_experience == 'none' and self.teaching_years in ['0-5', '6-15']:
            return "Beginner/Early Career"
        elif self.ai_experience in ['basic', 'intermediate'] and self.teaching_years in ['16-25', '25+']:
            return "Experienced/Learning AI"
        elif self.ai_experience == 'advanced':
            return "AI-Savvy Educator"
        else:
            return "Mixed Profile"
    
    def __str__(self):
        base_str = f"Session {self.session_id[:8]} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        if self.is_demographics_complete:
            return f"{base_str} ({self.user_profile_summary})"
        return base_str
    
    # Validation can be done at multiple levels:

    # 1. Model-level validation (add to UserSession class):
    def clean(self):
        """Model validation for demographics data"""
        from django.core.exceptions import ValidationError
        
        # Validate AI experience level
        valid_ai_levels = ['none', 'basic', 'intermediate', 'advanced']
        if self.ai_experience and self.ai_experience not in valid_ai_levels:
            raise ValidationError({
                'ai_experience': f'Invalid AI experience level. Must be one of: {valid_ai_levels}'
            })
        
        # Validate teaching years
        valid_teaching_years = ['0-5', '6-15', '16-25', '25+']
        if self.teaching_years and self.teaching_years not in valid_teaching_years:
            raise ValidationError({
                'teaching_years': f'Invalid teaching years. Must be one of: {valid_teaching_years}'
            })
        
        # Business logic validation
        if self.onboarding_completed and not (self.ai_experience and self.teaching_years):
            raise ValidationError(
                'Cannot mark onboarding as completed without both AI experience and teaching years data'
            )

    def save(self, *args, **kwargs):
        """Override save to add automatic validations"""
        self.full_clean()  # This calls clean() method
        
        # Auto-set completion time
        if self.onboarding_completed and not self.onboarding_completion_time:
            from django.utils import timezone
            self.onboarding_completion_time = timezone.now()
        
        super().save(*args, **kwargs)

    @property
    def training_profile_summary(self):
        """Summary of training needs for admin view"""
        if not self.training_needs_completed:
            return "Not completed"
        
        priorities = self.training_priorities
        if priorities:
            top_priority = min(priorities.items(), key=lambda x: x[1])[0] if priorities else "None"
            return f"Top: {top_priority}, {len(self.training_interests)} interests"
        return "No priorities set"
    
    @property 
    def research_participation_status(self):
        """Research participation summary"""
        if self.follow_up_email and self.research_interview_interest:
            return "Email + Interview"
        elif self.follow_up_email:
            return "Email only"
        elif self.research_interview_interest:
            return "Interview only"
        return "No participation"

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
    generated_prompt = models.TextField(blank=True, null=True)
    
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
    
    # === EDUCATIONAL DECISION PATTERNS ===
    
    # Subject Classification
    subject_category = models.CharField(
        max_length=50, 
        blank=True,
        choices=[
            ('STEM', 'Science, Technology, Engineering, Math'),
            ('Humanities', 'Language Arts, Social Studies, History'),
            ('Languages', 'Language Learning & Literature'),  # NEW
            ('Arts', 'Creative Arts, Music, Drama'),
            ('PE_Health', 'Physical Education & Health'),
            ('Life_Skills', 'Personal Development & Life Skills'),  # NEW
            ('Vocational', 'Career & Technical Education'),
            ('Cross_Curricular', 'Multiple Subjects'),
            ('Other', 'Other/Unspecified')
        ]
    )

    # Age Group Analysis
    age_group_category = models.CharField(
        max_length=30,
        blank=True,
        choices=[
            ('Early_Childhood', 'Ages 3-5'),
            ('Primary', 'Ages 6-11'), 
            ('Lower_Secondary', 'Ages 12-14'),
            ('Upper_Secondary', 'Ages 15-18'),
            ('Adult', 'Adult Learners'),
            ('Mixed', 'Mixed Age Groups')
        ]
    )

    # Methodology Classification
    methodology_category = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('Direct_Instruction', 'Teacher-led, explicit instruction'),
            ('Inquiry_Based', 'Student exploration and discovery'),
            ('Problem_Based', 'Real-world problem solving'),
            ('Collaborative', 'Group work and peer learning'),
            ('Project_Based', 'Extended project work'),
            ('Differentiated', 'Adaptive/personalized learning'),
            ('Assessment_Focused', 'Evaluation and feedback'),
            ('Technology_Enhanced', 'Digital tool integration')
        ]
    )

    # Complexity Assessment
    complexity_level = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('Basic', 'Simple, straightforward tasks'),
            ('Intermediate', 'Moderate complexity'),
            ('Advanced', 'Complex, multi-step processes'),
            ('Expert', 'Highly sophisticated approaches')
        ]
    )

    # Form Interaction Patterns
    form_start_time = models.DateTimeField(null=True, blank=True)
    form_completion_time = models.FloatField(null=True, blank=True)  # Total seconds
    field_change_count = models.IntegerField(default=0)  # How many edits
    help_visited_before = models.BooleanField(default=False)
    template_switches = models.IntegerField(default=0)  # Template changes during session

    theory_adoption_score = models.FloatField(null=True, blank=True)  # 0-10 scale
    #student_centeredness_score = models.FloatField(null=True, blank=True)  # 0-10 scale

    # === CONTENT ANALYSIS ===

    # Generated Content Metrics
    prompt_word_count = models.IntegerField(null=True, blank=True)
    prompt_sentence_count = models.IntegerField(null=True, blank=True)
    prompt_complexity_score = models.FloatField(null=True, blank=True)  # Readability index

    # Educational Theory Integration
    blooms_keywords_count = models.IntegerField(default=0)  # analyze, evaluate, create, etc.
    udl_keywords_count = models.IntegerField(default=0)     # multiple means, representation, etc.
    tpack_keywords_count = models.IntegerField(default=0)   # technology integration terms
    pedagogical_keywords_count = models.IntegerField(default=0)  # scaffolding, differentiation, etc.

    #theory_integration_score = models.FloatField(null=True, blank=True)  # Overall theory usage 0-10

    # Content Quality Indicators
    specificity_score = models.FloatField(null=True, blank=True)  # How specific vs generic
    actionability_score = models.FloatField(null=True, blank=True)  # How actionable for teachers
    #originality_score = models.FloatField(null=True, blank=True)   # How unique/creative

    # === CONTEXTUAL ADAPTATION PATTERNS ===

    # Learning Environment Considerations
    inclusion_indicators = models.JSONField(default=dict, blank=True)  # Special needs, ESL, etc.
    differentiation_strategies = models.JSONField(default=dict, blank=True)  # Multiple pathways
    assessment_integration = models.JSONField(default=dict, blank=True)  # How assessment is handled

    # Real-World Application
    practical_relevance_score = models.FloatField(null=True, blank=True)  # 0-10
    cross_curricular_connections = models.IntegerField(default=0)  # Links to other subjects

    # === REFLECTION & ITERATION PATTERNS ===

    # Metacognitive Behavior
    prompt_edited_after_generation = models.BooleanField(default=False)
    edit_count_before_copy = models.IntegerField(default=0)
    time_spent_reviewing = models.FloatField(null=True, blank=True)  # Seconds before copy

    # Professional Growth Indicators
    prompt_sophistication_trend = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ('Declining', 'Less sophisticated over time'),
            ('Stable', 'Consistent level'),
            ('Improving', 'More sophisticated over time'),
            ('Fluctuating', 'Variable quality')
        ]
    )

    # Session Context
    is_repeat_visitor = models.BooleanField(default=False)
    days_since_last_visit = models.IntegerField(null=True, blank=True)
    session_sequence_number = models.IntegerField(default=1)  # 1st, 2nd, 3rd visit etc.

    # Add these new fields to the PromptGeneration model in models.py
# Place them after the existing fields, before the __str__ method

    # === THEORY SELECTION TRACKING (NEW) ===
    
    # Theory Selection Analytics
    selected_theory = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        choices=[
            ('blooms', 'Bloom\'s Taxonomy'),
            ('udl', 'UDL Principles'),
            ('tpack', 'TPACK Framework'),
            ('constructivist', 'Constructivist Learning'),
            ('social_learning', 'Social Learning Theory'),
            ('scaffolding', 'Scaffolding'),
            ('differentiation', 'Differentiated Instruction'),
        ],
        help_text="Which educational theory was applied to enhance the prompt"
    )
    
    theory_auto_suggested = models.BooleanField(
        default=False,
        help_text="True if theory was auto-suggested by system, False if manually selected by user"
    )
    
    theory_suggestion_accuracy = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('accepted', 'User accepted auto-suggestion'),
            ('modified', 'User chose different theory than suggested'),
            ('ignored', 'User chose no theory when suggestion was made'),
            ('manual', 'User selected theory without seeing suggestion'),
        ],
        help_text="How user responded to system theory suggestions"
    )
    
    # Theory Usage Patterns (for longitudinal research)
    user_theory_preference = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        choices=[
            ('consistent', 'Always uses same theory'),
            ('varied_appropriate', 'Uses different theories appropriately'),
            ('experimental', 'Tries various theories to learn'),
            ('conservative', 'Sticks to basic theories'),
            ('advanced', 'Prefers complex/specialized theories'),
        ],
        help_text="Pattern analysis of user's theory selection behavior over time"
    )
    
    # Enhancement Quality Assessment
    theory_application_quality = models.FloatField(
        null=True, 
        blank=True,
        help_text="Quality score (0-10) for how well the theory was applied in context"
    )
    
    # Research Data Collection
    theory_learning_indicator = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('novice', 'Shows basic understanding of theories'),
            ('developing', 'Demonstrates growing theory knowledge'),
            ('proficient', 'Uses theories appropriately and effectively'),
            ('expert', 'Shows sophisticated theory integration'),
        ],
        help_text="User's apparent level of educational theory knowledge"
    )
    
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