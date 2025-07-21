from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from generator.views import index, generate_prompt, help_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),  # η αρχική σελίδα
    path('help/', help_page, name='help_page'),
    path('generate/', generate_prompt, name='generate_prompt'),  # για POST request
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('/static/', document_root='static')