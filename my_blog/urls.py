from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from dotenv import load_dotenv
import os

load_dotenv()
SECRET_ADMIN_PATH= os.getenv('SECRET_ADMIN_PATH')

urlpatterns = [
    path(f'{SECRET_ADMIN_PATH}/admin/', admin.site.urls),
    path('', include('blog.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout
    path('accounts/', include('blog.user_urls')),            # signup
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
