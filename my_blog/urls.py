from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from dotenv import load_dotenv
import os

load_dotenv()
secret_path= os.getenv('SECRET_PATH')

urlpatterns = [
    path(f'{secret_path}/admin/', admin.site.urls),
    path('', include('blog.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout
    path('accounts/', include('blog.user_urls')),            # signup
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
