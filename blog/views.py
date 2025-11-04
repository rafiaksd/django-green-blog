from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category, Tag
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect

from .forms import CommentForm
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.db.models import Q

def blog_list(request):
    posts = BlogPost.objects.all().order_by('-created_at')

    paginator = Paginator(posts, 6)  # 6 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, 'blog/blog_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
    })

def blog_detail(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    comments = blog_post.comments.all().order_by('-created_at')

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = blog_post
                comment.user = request.user
                comment.save()
                return redirect('blog_detail', slug=slug)
        else:
            return redirect('login')
    else:
        form = CommentForm()

    return render(request, 'blog/blog_detail.html', {
        'blog_post': blog_post,
        'comments': comments,
        'form': form
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def category_posts(request, slug=None):
    categories = Category.objects.all()
    tags = Tag.objects.all()
    selected_category = None

    # Check if deselect query param is present
    deselect = request.GET.get('deselect') == '1'

    if slug and not deselect:
        selected_category = get_object_or_404(Category, slug=slug)
        posts = BlogPost.objects.filter(category=selected_category).order_by('-created_at')
    else:
        posts = BlogPost.objects.all().order_by('-created_at')

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/blog_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'selected_category': selected_category,
    })


def tag_posts(request, slug=None):
    categories = Category.objects.all()
    tags = Tag.objects.all()
    selected_tag = None

    # Check if deselect query param is present
    deselect = request.GET.get('deselect') == '1'

    if slug and not deselect:
        selected_tag = get_object_or_404(Tag, slug=slug)
        posts = BlogPost.objects.filter(tags=selected_tag).order_by('-created_at')
    else:
        posts = BlogPost.objects.all().order_by('-created_at')

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/blog_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'selected_tag': selected_tag,
    })


def search_posts(request):
    query = request.GET.get('q')
    posts = BlogPost.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-created_at') if query else BlogPost.objects.none()

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    tags = Tag.objects.all()

    return render(request, 'blog/blog_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'search_query': query,
    })