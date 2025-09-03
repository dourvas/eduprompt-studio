from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from generator import views  # ΑΛΛΑΓΗ ΕΔΩ

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('help/', views.help_page, name='help_page'),
    path('generate/', views.generate_prompt, name='generate_prompt'),
    path('track-copy/', views.track_copy, name='track_copy'),
    path('onboarding/', views.onboarding_data_collection, name='onboarding_data'),
    path('onboarding/stats/', views.onboarding_stats, name='onboarding_stats'),
    path('training-needs/', views.training_needs_data_collection, name='training_needs_data'),
    path('training-needs/stats/', views.training_needs_stats, name='training_needs_stats')
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('/static/', document_root='static')