from django.contrib import admin
from django.db.models import Count, Avg, Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import UserSession, PromptGeneration, PageView, TemplateUsage, ImprovementSuggestion


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
    'session_id_short', 'start_time', 'duration_minutes', 'pages_visited', 
    'completion_status', 'demographics_summary', 'onboarding_status', 
    'training_needs_status', 'research_participation_summary', 'research_category'
]
    
    list_filter = [
        'completion_status', 'start_time', 'onboarding_completed', 'onboarding_skipped',
        'ai_experience', 'teaching_years',
        # NEW PHASE 2 FILTERS
        'training_needs_completed', 'training_needs_shown', 'research_interview_interest'
    ]
    
    search_fields = ['session_id', 'contact_email', 'follow_up_email']  # UPDATED
    
    readonly_fields = [
        'session_id', 'start_time', 'last_activity', 'duration_minutes',
        'onboarding_completion_time', 'training_needs_completion_time',  # NEW
        'user_profile_summary', 'research_participant_type', 'training_profile_summary'  # NEW
    ]
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'start_time', 'last_activity', 'duration_minutes', 
                      'pages_visited', 'completion_status')
        }),
        ('Phase 1: Demographics & Onboarding', {
            'fields': ('ai_experience', 'teaching_years', 'onboarding_completed', 
                      'onboarding_completion_time', 'onboarding_skipped', 'research_consent'),
            'classes': ('collapse',)
        }),
        ('Phase 2: Training Needs Survey', {  # NEW SECTION
            'fields': ('training_needs_completed', 'training_needs_completion_time', 
                      'training_needs_shown', 'training_interests', 'training_priorities', 
                      'training_other_needs'),
            'classes': ('collapse',)
        }),
        ('Research Participation & Contact', {  # UPDATED SECTION
            'fields': ('contact_email', 'follow_up_email', 'research_interview_interest'),
            'classes': ('collapse',)
        }),
        ('Technical Data', {
            'fields': ('referrer', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Computed Properties', {
            'fields': ('user_profile_summary', 'research_participant_type', 'training_profile_summary'),  # UPDATED
            'classes': ('collapse',)
        })
    )
    
    def session_id_short(self, obj):
        return obj.session_id[:8] + '...'
    session_id_short.short_description = 'Session ID'

    def demographics_summary(self, obj):
        if not obj.is_demographics_complete:
            return format_html('<span style="color: #999; font-style: italic;">No data</span>')
        
        ai_color = {
            'none': '#dc2626',      # Red
            'basic': '#f59e0b',     # Amber  
            'intermediate': '#3b82f6', # Blue
            'advanced': '#059669'    # Green
        }.get(obj.ai_experience, '#6b7280')
        
        teaching_color = {
            '0-5': '#ec4899',       # Pink (new)
            '6-15': '#8b5cf6',      # Purple (developing)
            '16-25': '#3b82f6',     # Blue (experienced)
            '25+': '#059669'        # Green (veteran)
        }.get(obj.teaching_years, '#6b7280')
        
        return format_html(
            '<div style="display: flex; gap: 8px;">'
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>'
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>'
            '</div>',
            ai_color, obj.get_ai_experience_display() if obj.ai_experience else '',
            teaching_color, obj.get_teaching_years_display() if obj.teaching_years else ''
        )
    demographics_summary.short_description = 'Demographics'
    
    def onboarding_status(self, obj):
        if obj.onboarding_completed:
            return format_html(
                '<span style="color: #059669; font-weight: bold;">✓ Complete</span><br>'
                '<small style="color: #6b7280;">{}</small>',
                obj.onboarding_completion_time.strftime('%m/%d %H:%M') if obj.onboarding_completion_time else ''
            )
        elif obj.onboarding_skipped:
            return format_html('<span style="color: #f59e0b;">⏭ Skipped</span>')
        else:
            return format_html('<span style="color: #6b7280;">⏳ Pending</span>')
    onboarding_status.short_description = 'Onboarding'
    
    def research_category(self, obj):
        category = obj.research_participant_type
        color_map = {
            'Beginner/Early Career': '#ec4899',
            'Experienced/Learning AI': '#3b82f6', 
            'AI-Savvy Educator': '#059669',
            'Mixed Profile': '#8b5cf6',
            'Unknown': '#6b7280'
        }
        
        color = color_map.get(category, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; white-space: nowrap;">{}</span>',
            color, category
        )
    research_category.short_description = 'Research Category'
    
    # Add custom actions
    actions = ['mark_research_consent', 'export_demographics_csv', 'export_training_needs_csv']
    
    def mark_research_consent(self, request, queryset):
        """Mark selected sessions as having research consent"""
        updated = queryset.update(research_consent=True)
        self.message_user(request, f'{updated} sessions marked with research consent.')
    mark_research_consent.short_description = 'Mark as research consented'
    
    def export_demographics_csv(self, request, queryset):
        """Export demographics data as CSV for research"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="demographics_data.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Session ID', 'Start Time', 'AI Experience', 'Teaching Years', 
            'Research Category', 'Onboarding Completed', 'Contact Email',
            'Duration (min)', 'Pages Visited'
        ])
        
        for session in queryset:
            writer.writerow([
                session.session_id[:8],
                session.start_time.strftime('%Y-%m-%d %H:%M'),
                session.get_ai_experience_display() if session.ai_experience else '',
                session.get_teaching_years_display() if session.teaching_years else '',
                session.research_participant_type,
                session.onboarding_completed,
                session.contact_email or '',
                session.duration_minutes,
                session.pages_visited
            ])
        
        return response
    export_demographics_csv.short_description = 'Export demographics as CSV'

    def export_training_needs_csv(self, request, queryset):
        """Export training needs data as CSV for research"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="training_needs_data.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Session ID', 'Completion Time', 'AI Experience', 'Teaching Years',
            'Training Interests', 'Priority 1', 'Priority 2', 'Priority 3',
            'Other Needs', 'Follow-up Email', 'Interview Interest'
    ])
    
        for session in queryset.filter(training_needs_completed=True):
            # Get priorities by rank
            priorities = session.training_priorities or {}
            priority_1 = next((area for area, rank in priorities.items() if rank == 1), '')
            priority_2 = next((area for area, rank in priorities.items() if rank == 2), '')
            priority_3 = next((area for area, rank in priorities.items() if rank == 3), '')
            
            writer.writerow([
                session.session_id[:8],
                session.training_needs_completion_time.strftime('%Y-%m-%d %H:%M') if session.training_needs_completion_time else '',
                session.get_ai_experience_display() if session.ai_experience else '',
                session.get_teaching_years_display() if session.teaching_years else '',
                ', '.join(session.training_interests or []),
                priority_1,
                priority_2,
                priority_3,
                session.training_other_needs or '',
                session.follow_up_email or '',
                'Yes' if session.research_interview_interest else 'No'
            ])
    
        return response
    export_training_needs_csv.short_description = 'Export training needs as CSV'
    
    # UPDATED: Enhanced changelist with Phase 2 statistics
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Existing statistics code
        total_sessions = UserSession.objects.count()
        completed_onboarding = UserSession.objects.filter(onboarding_completed=True).count()
        
        extra_context.update({
            'onboarding_stats': {
                'total_sessions': total_sessions,
                'completed': completed_onboarding,
            },
            'inject_modal_script': True  # Flag για το template
        })
        
        return super().changelist_view(request, extra_context)

    def inject_modal_view(self, request):
        """Simple view to inject modal script"""
        script = '''
        <script>
        if (!window.sessionModalLoaded) {
            window.sessionModalLoaded = true;
            
            // Create modal HTML
            const modalHTML = `
            <div id="sessionAnalyticsModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; justify-content: center; align-items: center;">
            <div style="background: white; border-radius: 12px; padding: 20px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
                <h2>📊 Session Analytics</h2>
                <p>Session ID: <span id="modalSessionId"></span></p>
                <button onclick="closeSessionModal()">Close</button>
            </div>
            </div>`;
            
            document.body.insertAdjacentHTML('beforeend', modalHTML);
            
            // Add functions
            window.openSessionModal = function(sessionId) {
                document.getElementById('sessionAnalyticsModal').style.display = 'flex';
                document.getElementById('modalSessionId').textContent = sessionId;
                console.log('Modal opened for:', sessionId);
            }
            
            window.closeSessionModal = function() {
                document.getElementById('sessionAnalyticsModal').style.display = 'none';
            }
        }
        </script>
        '''
        
        from django.http import HttpResponse
        return HttpResponse(script, content_type='text/html')
    # NEW METHOD: Training needs status display
    def training_needs_status(self, obj):
        if obj.training_needs_completed:
            interests_count = len(obj.training_interests) if obj.training_interests else 0
            priorities_count = len(obj.training_priorities) if obj.training_priorities else 0
            return format_html(
                '<span style="color: #059669; font-weight: bold;">✓ Complete</span><br>'
                '<small style="color: #6b7280;">{} interests, {} priorities</small>',
                interests_count, priorities_count
            )
        elif obj.training_needs_shown:
            return format_html('<span style="color: #f59e0b;">⏭ Shown but not completed</span>')
        else:
            return format_html('<span style="color: #6b7280;">⏳ Not shown</span>')
    training_needs_status.short_description = 'Training Needs'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Basic statistics για το dashboard
        total_sessions = UserSession.objects.count()
        completed_onboarding = UserSession.objects.filter(onboarding_completed=True).count()
        completed_training = UserSession.objects.filter(training_needs_completed=True).count()
        
        extra_context.update({
            'onboarding_stats': {
                'total_sessions': total_sessions,
                'completed': completed_onboarding,
            },
            'training_stats': {
                'completed': completed_training,
                'completion_rate': round((completed_training / total_sessions * 100), 1) if total_sessions > 0 else 0,
            },
            #'session_modal_html': self.get_session_modal_html(),
            'inject_modal_script': True,
            'training_analytics_button': True,  # ΝΕΟ: Για το training analytics button
        })
        
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('inject-modal/', self.inject_modal_view, name='inject_modal'),  # ΥΠΑΡΧΟΝ
            path('training-analytics/', 
                self.admin_site.admin_view(self.training_analytics_dashboard), 
                name='training_analytics_dashboard'),  # ΠΡΟΣΘΕΣΤΕ ΑΥΤΟ
            path('training-analytics-data/', 
                self.admin_site.admin_view(self.training_analytics_data), 
                name='training_analytics_data'),  # ΚΑΙ ΑΥΤΟ
        ]
        return custom_urls + urls
    
    # NEW METHOD: Research participation summary
    def research_participation_summary(self, obj):
        parts = []
        
        if obj.follow_up_email:
            parts.append('<span style="color: #3b82f6;">📧 Email</span>')
        
        if obj.research_interview_interest:
            parts.append('<span style="color: #059669;">🎤 Interview</span>')
        
        if not parts:
            return format_html('<span style="color: #9ca3af;">No participation</span>')
        
        return format_html(' '.join(parts))
    research_participation_summary.short_description = 'Research Participation'

    def view_analytics_button(self, obj):
        return format_html(
            '<button onclick="alert(\'Session Analytics for: {}\'); '
            'window.open(\'/session-analytics/{}/\', \'_blank\', \'width=800,height=600\'); return false;" '
            'class="button" style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%); '
            'color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; '
            'font-size: 11px;">📊 View Analytics</button>',
            obj.session_id[:8], obj.session_id
        )
    view_analytics_button.short_description = 'Analytics'
    view_analytics_button.allow_tags = True

    def training_analytics_dashboard(self, request):
        """Συνολικό dashboard για όλα τα training needs data"""
        return render(request, 'admin/training_analytics_dashboard.html', {
            'title': 'Training Needs Analytics Dashboard',
            'site_title': 'EduPrompt Studio Research Analytics',
        })

    def training_analytics_data(self, request):
        """API endpoint για training analytics data"""
        # Συλλογή δεδομένων από όλα τα completed training needs
        completed_sessions = UserSession.objects.filter(training_needs_completed=True)
        total_sessions = UserSession.objects.count()
        
        # Στατιστικά
        completion_rate = round((completed_sessions.count() / total_sessions * 100), 1) if total_sessions > 0 else 0
        email_provided = completed_sessions.exclude(follow_up_email__isnull=True).exclude(follow_up_email='').count()
        interview_interest = completed_sessions.filter(research_interview_interest=True).count()
        
        # Συλλογή interests
        all_interests = []
        all_priorities = {}
        for session in completed_sessions:
            all_interests.extend(session.training_interests or [])
            for area, priority in (session.training_priorities or {}).items():
                if priority == 1:  # Top priorities only
                    all_priorities[area] = all_priorities.get(area, 0) + 1
        
        from collections import Counter
        interests_distribution = dict(Counter(all_interests).most_common())
        
        data = {
            'completion_rate': completion_rate,
            'email_rate': round((email_provided / completed_sessions.count() * 100), 1) if completed_sessions.count() > 0 else 0,
            'interview_rate': round((interview_interest / completed_sessions.count() * 100), 1) if completed_sessions.count() > 0 else 0,
            'avg_priorities': round(sum(len(s.training_priorities or {}) for s in completed_sessions) / completed_sessions.count(), 1) if completed_sessions.count() > 0 else 0,
            'interests_distribution': interests_distribution,
            'priorities_distribution': all_priorities,
            'participation_stats': {
                'both': completed_sessions.filter(research_interview_interest=True).exclude(follow_up_email__isnull=True).exclude(follow_up_email='').count(),
                'email_only': completed_sessions.exclude(follow_up_email__isnull=True).exclude(follow_up_email='').filter(research_interview_interest=False).count(),
                'interview_only': completed_sessions.filter(research_interview_interest=True, follow_up_email__isnull=True).count(),
                'none': completed_sessions.filter(research_interview_interest=False, follow_up_email__isnull=True).count()
            }
        }
        
        return JsonResponse(data)
class Media:
    js = ('generator/session_analytics.js',)
    css = {
        'all': ('admin/css/custom_admin.css',)  # Optional: custom CSS
    }

    def get_session_modal_html(self):
        """Include session analytics modal in admin"""
        from django.template.loader import render_to_string
        return render_to_string('admin/session_analytics_modal.html')


@admin.register(PromptGeneration)
class PromptGenerationAdmin(admin.ModelAdmin):
    change_list_template = 'admin/generator/promptgeneration/change_list.html'
    list_display = [
        'id', 'timestamp', 'template_used', 'task_short', 'enhancement_mode', 
        'success', 'copied_to_clipboard', 'response_time_seconds',
        'subject_category_colored', 'age_group_category', 'complexity_level_colored',
        'selected_theory_colored', 'theory_auto_suggested_icon'
    ]
    
    list_filter = [
        'enhancement_mode', 'success', 'copied_to_clipboard', 'template_used', 
        'subject_category', 'age_group_category', 'methodology_category',
        'complexity_level', 'timestamp',
        'selected_theory', 'theory_auto_suggested'
    ]
    
    search_fields = ['subject', 'task', 'role', 'generated_prompt']
    readonly_fields = ['timestamp', 'response_time_seconds']
    date_hierarchy = 'timestamp'
    
    # NEW: Custom URLs για Analytics Dashboard
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('theory-analytics/', 
                 self.admin_site.admin_view(self.theory_analytics_view), 
                 name='theory_analytics_dashboard'),
            path('theory-analytics/data/', 
                 self.admin_site.admin_view(self.theory_analytics_data), 
                 name='theory_analytics_data'),
        ]
        return custom_urls + urls
    
    # NEW: Theory Analytics Dashboard View
    def theory_analytics_view(self, request):
        """Main dashboard view with charts"""
        context = {
            'title': 'Theory Selection Analytics Dashboard',
            'site_title': 'EduPrompt Studio Analytics',
            'has_permission': True,
            'opts': self.model._meta,
        }
        return render(request, 'admin/theory_analytics_dashboard.html', context)
    
    # NEW: JSON Data API για Charts
    def theory_analytics_data(self, request):
        """API endpoint που επιστρέφει JSON data για charts"""
        analytics_data = AnalyticsSummary.get_summary()
        
        # Format data για Chart.js
        chart_data = {
            'theory_distribution': {
                'labels': [item['selected_theory'] for item in analytics_data['theory_distribution']],
                'data': [item['count'] for item in analytics_data['theory_distribution']],
                'colors': [
                    '#7C3AED',  # blooms - Purple
                    '#059669',  # udl - Emerald
                    '#DC2626',  # tpack - Red
                    '#D97706',  # constructivist - Amber
                    '#2563EB',  # social_learning - Blue
                    '#16A34A',  # scaffolding - Green
                    '#C2410C'   # differentiation - Orange
                ]
            },
            'selection_method': {
                'labels': ['Auto-Suggested', 'Manual Selection'],
                'data': [
                    analytics_data['theory_selection_method']['auto_suggested'],
                    analytics_data['theory_selection_method']['manual_selected']
                ],
                'colors': ['#059669', '#DC2626']
            },
            'theory_effectiveness': {
                'labels': [item['selected_theory'] for item in analytics_data['theory_effectiveness']],
                'total_usage': [item['total_usage'] for item in analytics_data['theory_effectiveness']],
                'copied_count': [item['copied_count'] for item in analytics_data['theory_effectiveness']],
                'effectiveness_rate': [
                    round((item['copied_count'] / item['total_usage'] * 100), 1) if item['total_usage'] > 0 else 0
                    for item in analytics_data['theory_effectiveness']
                ]
            },
            'basic_stats': {
                'total_sessions': analytics_data['total_sessions'],
                'total_prompts': analytics_data['total_prompts'],
                'success_rate': analytics_data['success_rate'],
                'copy_rate': analytics_data['copy_rate'],
                'auto_suggestion_rate': analytics_data['theory_selection_method']['auto_suggestion_rate']
            }
        }
        
        return JsonResponse(chart_data)
    
    def task_short(self, obj):
        return obj.task[:50] + '...' if len(obj.task) > 50 else obj.task
    task_short.short_description = 'Task'
    
    def subject_category_colored(self, obj):
        colors = {
            'STEM': '#3B82F6',  # Blue
            'Humanities': '#8B5CF6',  # Purple  
            'Arts': '#EC4899',  # Pink
            'Languages': '#06B6D4',  # Cyan
            'PE_Health': '#10B981',  # Green
            'Life_Skills': '#F97316',  # Orange
            'Vocational': '#F59E0B',  # Amber
            'Cross_Curricular': '#6B7280',  # Gray
            'Other': '#9CA3AF'  # Light Gray
        }
        color = colors.get(obj.subject_category, '#9CA3AF')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.subject_category or 'N/A'
        )
    subject_category_colored.short_description = 'Subject'
    subject_category_colored.admin_order_field = 'subject_category'
    
    def complexity_level_colored(self, obj):
        colors = {
            'Basic': '#10B981',  # Green
            'Intermediate': '#F59E0B',  # Amber
            'Advanced': '#EF4444',  # Red
            'Expert': '#7C3AED'  # Purple
        }
        color = colors.get(obj.complexity_level, '#9CA3AF')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.complexity_level or 'N/A'
        )
    complexity_level_colored.short_description = 'Complexity'
    complexity_level_colored.admin_order_field = 'complexity_level'
    
    def selected_theory_colored(self, obj):
        theory_colors = {
            'blooms': '#7C3AED',  # Purple - Cognitive
            'udl': '#059669',  # Emerald - Inclusive
            'tpack': '#DC2626',  # Red - Technology
            'constructivist': '#D97706',  # Amber - Discovery
            'social_learning': '#2563EB',  # Blue - Social
            'scaffolding': '#16A34A',  # Green - Support
            'differentiation': '#C2410C'  # Orange - Individual
        }
        
        theory_names = {
            'blooms': 'Bloom\'s',
            'udl': 'UDL',
            'tpack': 'TPACK', 
            'constructivist': 'Constructivist',
            'social_learning': 'Social Learning',
            'scaffolding': 'Scaffolding',
            'differentiation': 'Differentiation'
        }
        
        if not obj.selected_theory:
            return format_html('<span style="color: #9CA3AF; font-style: italic;">None</span>')
            
        color = theory_colors.get(obj.selected_theory, '#9CA3AF')
        name = theory_names.get(obj.selected_theory, obj.selected_theory)
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">{}</span>',
            color, name
        )
    selected_theory_colored.short_description = 'Theory Applied'
    selected_theory_colored.admin_order_field = 'selected_theory'
    
    def theory_auto_suggested_icon(self, obj):
        if obj.theory_auto_suggested:
            return format_html(
                '<span style="color: #059669; font-size: 14px;" title="Theory was auto-suggested by system">🤖</span>'
            )
        elif obj.selected_theory:
            return format_html(
                '<span style="color: #DC2626; font-size: 14px;" title="Theory was manually selected by user">👤</span>'
            )
        else:
            return format_html('<span style="color: #9CA3AF;">-</span>')
    theory_auto_suggested_icon.short_description = 'Selection Type'
    theory_auto_suggested_icon.admin_order_field = 'theory_auto_suggested'

@admin.register(TemplateUsage)
class TemplateUsageAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'usage_count', 'last_used', 'usage_percentage', 'popularity_bar']
    readonly_fields = ['last_used']
    ordering = ['-usage_count']
    
    def usage_percentage(self, obj):
        total = sum(t.usage_count for t in TemplateUsage.objects.all())
        if total == 0:
            return "0%"
        percentage = (obj.usage_count / total) * 100
        return f"{percentage:.1f}%"
    usage_percentage.short_description = 'Usage %'
    
    def popularity_bar(self, obj):
        max_usage = TemplateUsage.objects.first().usage_count if TemplateUsage.objects.exists() else 1
        width = int((obj.usage_count / max_usage) * 100) if max_usage > 0 else 0
        
        return format_html(
            '<div style="width: 100px; background-color: #E5E7EB; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; height: 12px; background-color: #3B82F6; border-radius: 3px;"></div>'
            '</div>',
            width
        )
    popularity_bar.short_description = 'Popularity'

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'path', 'method', 'session_short']
    list_filter = ['path', 'method', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def session_short(self, obj):
        return obj.session.session_id[:8] + '...'
    session_short.short_description = 'Session'

@admin.register(ImprovementSuggestion)
class ImprovementSuggestionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'applied', 'suggestion_preview']
    list_filter = ['applied', 'timestamp']
    
    def suggestion_preview(self, obj):
        return obj.suggestion_text[:100] + '...' if len(obj.suggestion_text) > 100 else obj.suggestion_text
    suggestion_preview.short_description = 'Suggestion Preview'

# Enhanced Analytics Summary with Theory Selection Data
class AnalyticsSummary:
    """Enhanced analytics summary with educational research metrics including theory selection"""
    
    @staticmethod
    def get_summary():
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # Basic stats
        total_sessions = UserSession.objects.count()
        total_prompts = PromptGeneration.objects.count()
        successful_prompts = PromptGeneration.objects.filter(success=True).count()
        copied_prompts = PromptGeneration.objects.filter(copied_to_clipboard=True).count()
        
        # Weekly stats
        weekly_sessions = UserSession.objects.filter(start_time__date__gte=week_ago).count()
        weekly_prompts = PromptGeneration.objects.filter(timestamp__date__gte=week_ago).count()
        
        # Popular templates
        popular_templates = TemplateUsage.objects.order_by('-usage_count')[:5]
        
        # Enhancement mode usage
        enhancement_stats = PromptGeneration.objects.values('enhancement_mode').annotate(count=Count('id'))
        
        # Educational Classification Statistics
        subject_distribution = PromptGeneration.objects.exclude(
            subject_category__isnull=True
        ).values('subject_category').annotate(count=Count('id')).order_by('-count')
        
        age_group_distribution = PromptGeneration.objects.exclude(
            age_group_category__isnull=True
        ).values('age_group_category').annotate(count=Count('id')).order_by('-count')
        
        methodology_distribution = PromptGeneration.objects.exclude(
            methodology_category__isnull=True
        ).values('methodology_category').annotate(count=Count('id')).order_by('-count')
        
        complexity_distribution = PromptGeneration.objects.exclude(
            complexity_level__isnull=True
        ).values('complexity_level').annotate(count=Count('id')).order_by('-count')
        
        # Theory Selection Analytics
        theory_distribution = PromptGeneration.objects.exclude(
            selected_theory__isnull=True
        ).exclude(selected_theory='').values('selected_theory').annotate(count=Count('id')).order_by('-count')
        
        # Theory Auto-suggestion vs Manual Selection
        theory_selection_method = PromptGeneration.objects.exclude(
            selected_theory__isnull=True
        ).exclude(selected_theory='').aggregate(
            total_with_theory=Count('id'),
            auto_suggested=Count('id', filter=Q(theory_auto_suggested=True)),
            manual_selected=Count('id', filter=Q(theory_auto_suggested=False))
        )
        
        # Theory effectiveness (theories used with copied prompts)
        theory_effectiveness = PromptGeneration.objects.exclude(
            selected_theory__isnull=True
        ).exclude(selected_theory='').values('selected_theory').annotate(
            total_usage=Count('id'),
            copied_count=Count('id', filter=Q(copied_to_clipboard=True))
        ).order_by('-copied_count')
        
        # Enhanced vs Basic mode with theories
        enhancement_theory_cross = PromptGeneration.objects.exclude(
            selected_theory__isnull=True
        ).exclude(selected_theory='').values('enhancement_mode', 'selected_theory').annotate(count=Count('id'))
                 
        # Content Analysis Averages
        avg_content_metrics = PromptGeneration.objects.aggregate(
            avg_words=Avg('prompt_word_count'),
            avg_complexity=Avg('prompt_complexity_score'),
            avg_specificity=Avg('specificity_score'),
            avg_actionability=Avg('actionability_score')
        )
        
        # Theory Integration Analysis
        theory_keyword_stats = PromptGeneration.objects.aggregate(
            avg_blooms=Avg('blooms_keywords_count'),
            avg_udl=Avg('udl_keywords_count'),
            avg_tpack=Avg('tpack_keywords_count'),
            avg_pedagogical=Avg('pedagogical_keywords_count')
        )
        
        return {
            # Basic metrics
            'total_sessions': total_sessions,
            'total_prompts': total_prompts,
            'success_rate': f"{(successful_prompts/total_prompts*100):.1f}%" if total_prompts > 0 else "0%",
            'copy_rate': f"{(copied_prompts/total_prompts*100):.1f}%" if total_prompts > 0 else "0%",
            'weekly_sessions': weekly_sessions,
            'weekly_prompts': weekly_prompts,
            'popular_templates': popular_templates,
            'enhancement_stats': enhancement_stats,
            
            # Educational Analytics
            'subject_distribution': subject_distribution,
            'age_group_distribution': age_group_distribution,
            'methodology_distribution': methodology_distribution,
            'complexity_distribution': complexity_distribution,
            
            # Theory Selection Analytics
            'theory_distribution': theory_distribution,
            'theory_selection_method': {
                'total_with_theory': theory_selection_method['total_with_theory'] or 0,
                'auto_suggested': theory_selection_method['auto_suggested'] or 0,
                'manual_selected': theory_selection_method['manual_selected'] or 0,
                'auto_suggestion_rate': f"{(theory_selection_method['auto_suggested'] / theory_selection_method['total_with_theory'] * 100):.1f}%" if theory_selection_method['total_with_theory'] > 0 else "0%"
            },
            'theory_effectiveness': theory_effectiveness,
            'enhancement_theory_cross': enhancement_theory_cross,
                        
            # Content Metrics
            'avg_content_metrics': {
                'words': round(avg_content_metrics['avg_words'] or 0, 1),
                'complexity': round(avg_content_metrics['avg_complexity'] or 0, 2),
                'specificity': round(avg_content_metrics['avg_specificity'] or 0, 2),
                'actionability': round(avg_content_metrics['avg_actionability'] or 0, 2)
            },
            
            # Theory Integration
            'theory_keywords': {
                'blooms': round(theory_keyword_stats['avg_blooms'] or 0, 1),
                'udl': round(theory_keyword_stats['avg_udl'] or 0, 1),
                'tpack': round(theory_keyword_stats['avg_tpack'] or 0, 1),
                'pedagogical': round(theory_keyword_stats['avg_pedagogical'] or 0, 1)
            }
        }