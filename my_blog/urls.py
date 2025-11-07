from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from dotenv import load_dotenv
import os

load_dotenv()
SECRET_ADMIN_PATH = os.getenv('SECRET_ADMIN_PATH')
# Conditionally build the admin path
admin_path = f'{SECRET_ADMIN_PATH}/admin/' if SECRET_ADMIN_PATH else 'admin/'

urlpatterns = [
    path('greenblog/', include([
        path(admin_path, admin.site.urls),
        path('', include('blog.urls')),  # your blog URLs now under /greenblog/
        path('accounts/', include('django.contrib.auth.urls')),
        path('accounts/', include('blog.user_urls')),
    ])),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
