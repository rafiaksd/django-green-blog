from django.urls import path
from . import views
from .views import upload_ckeditor_image

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('tag/<slug:slug>/', views.tag_posts, name='tag_posts'),
    path('search/', views.search_posts, name='search_posts'),

    # post by ID + optional slug
    path('post/<int:id>/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('post/<int:id>/', views.blog_detail, name='blog_detail_id'),

    path('ckeditor/upload/', upload_ckeditor_image, name='ckeditor-upload'),
    path('about/', views.about, name='about'),

    path('comment/<int:pk>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]
