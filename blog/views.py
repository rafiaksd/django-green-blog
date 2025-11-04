from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category, Tag
from .forms import CustomUserCreationForm
from django.shortcuts import redirect

from .forms import CommentForm
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.db.models import Q

import re, html

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

def embed_video(content):
    """This function takes content and converts YouTube, Vimeo, X (Twitter) links inside <a> tags into iframe or blockquote embeds."""
    
    # Replace YouTube links inside <a> tags with iframe embed
    content = re.sub(
        r'<a href="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)"(.*)>(.*?)</a>',
        r'<iframe width="800" height="450" src="https://www.youtube.com/embed/\1" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
        content
    )

    # Replace Vimeo links inside <a> tags with iframe embed
    content = re.sub(
        r'<a href="https://vimeo\.com/(\d+)"(.*)>(.*?)</a>',
        r'<iframe src="https://player.vimeo.com/video/\1" width="800" height="450" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>',
        content
    )

    # Replace X (Twitter) links inside <a> tags with blockquote embed
    content = re.sub(
        r'<a href="https://x\.com/([a-zA-Z0-9_]+)/status/(\d+)"(.*)>(.*?)</a>',
        r'<blockquote class="twitter-tweet"><p lang="en" dir="ltr"><a style="width: 200px; margin-left:auto; margin-right: auto;" href="https://twitter.com/\1/status/\2"></a></p></blockquote><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>',
        content
    )

    
    # Print the content before Facebook processing
    print(f"LAST TRY before FACEBOOK: ")
    print(f"CURRENT CONTENT IS: {content}")
    print()
    print()

    # Replace Facebook iframe links inside <a> tags with iframe embed
    content = re.sub(
        r'<a href="https://www\.facebook\.com/plugins/post\.php\?href=([^\"]+)"(.*)>(.*?)</a>',
        r'<iframe src="https://www.facebook.com/plugins/post.php?href=\1" width="500" height="498" style="border:none;overflow:hidden" scrolling="no" frameborder="0" allowfullscreen="true" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" />',
        content
    )

    content = html.unescape(content)

    # Print the final content after processing
    print(f"FINAL CONTENT AFTER FACEBOOK PROCESSING:\n\n {content}")

    return content

def blog_detail(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    comments = blog_post.comments.all().order_by('-created_at')

    # Process the content to embed videos
    blog_post.content = embed_video(blog_post.content)

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
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
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
    ).order_by('-created_at')

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