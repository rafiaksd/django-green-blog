from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('tag/<slug:slug>/', views.tag_posts, name='tag_posts'),
    path('search/', views.search_posts, name='search_posts'),
    path('post/<slug:slug>/', views.blog_detail, name='blog_detail'),
]
