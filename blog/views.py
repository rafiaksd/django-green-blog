from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category, Tag
from .forms import CustomUserCreationForm
from django.shortcuts import redirect

from .forms import CommentForm
from django.contrib.auth.decorators import login_required

from django.core.paginator import Paginator
from django.db.models import Q

from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import default_storage
import re, html, os
from PIL import Image
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def upload_ckeditor_image(request):
    """ Handle image upload from CKEditor """
    if request.method == 'POST' and request.FILES.get('upload'):
        image = request.FILES['upload']
        path = default_storage.save(f"blog_images/{image.name}", image)

        # Get the full file path where the image is saved
        img_path = os.path.join(settings.MEDIA_ROOT, path)

        try:
            # Open the image to check its size
            img = Image.open(img_path)
            # Check if image size is greater than 1MB
            if os.path.getsize(img_path) > 1024 * 1024:  # 1 MB
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                img.save(img_path, optimize=True, quality=70)
                print(f"Image {image.name} resized successfully")
            else:
                print(f"Image {image.name} is under 1MB, no resizing needed")
        except Exception as e:
            if os.path.exists(img_path):
                os.remove(img_path)
            print(f"Error during resizing: {e}")
            pass

        # Respond with the image URL
        image_url = os.path.join(settings.MEDIA_URL, path)
        return JsonResponse({
            'uploaded': 1,
            'fileName': image.name,
            'url': image_url  # This URL is what CKEditor will use to display the image
        })
    return JsonResponse({'uploaded': 0, 'error': {'message': 'Image upload failed'}})

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