from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from generator import views

urlpatterns = [
    path('', views.index, name='index'),
    path('help/', views.help_page, name='help_page'),
    path('generate/', views.generate_prompt, name='generate_prompt'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
