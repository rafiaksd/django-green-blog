from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
import os
from dotenv import load_dotenv

from django.conf import settings
from django.conf.urls.static import static

load_dotenv()
SECRET_ADMIN_PATH = os.getenv('SECRET_ADMIN_PATH')
admin_path = f"{SECRET_ADMIN_PATH}/admin/" if SECRET_ADMIN_PATH else "admin/"

# wrapper view
def admin_redirect(request):
    return redirect(f"/greenblog/{admin_path}")

urlpatterns = [
    # Admin redirect with a name
    path('greenblog/admin-panel/', admin_redirect, name='admin_panel'),

    # Admin site actual URLs
    path(f'greenblog/{admin_path}', admin.site.urls),

    # Blog and auth
    path('greenblog/', include('blog.urls')),
    path('greenblog/accounts/', include('django.contrib.auth.urls')),
    path('greenblog/accounts/', include('blog.user_urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)