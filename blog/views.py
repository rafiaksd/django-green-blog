from django.shortcuts import render, get_object_or_404
from .models import BlogPost, Category, Tag
from .forms import CustomUserCreationForm
from django.shortcuts import redirect

from .models import Comment
from .forms import CommentForm
from django.http import HttpResponseForbidden
from django.contrib import messages

from django.core.paginator import Paginator
from django.db.models import Q

from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import default_storage

import os
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
                print(f"📷✅ CKEDITOR Image {image.name} resized successfully")
            else:
                print(f"📷 CKEDITOR Image {image.name} is under 1MB, no resizing needed")
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
    posts = BlogPost.objects.filter(publish=True).order_by('-created_at')

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

def blog_detail(request, id, slug=None):
    blog_post = get_object_or_404(BlogPost, id=id, publish=True)
    comments = blog_post.comments.all().order_by('-created_at')

    # if slug is outdated, redirect to canonical URL
    if slug != blog_post.slug:
        return redirect(blog_post.get_absolute_url(), permanent=True)
    
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = blog_post
                comment.user = request.user
                comment.save()
                return redirect(blog_post.get_absolute_url())
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
        posts = BlogPost.objects.filter(publish=True,category=selected_category).order_by('-created_at')
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
        posts = BlogPost.objects.filter(publish=True, tags=selected_tag).order_by('-created_at')
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
    ).filter(publish=True).order_by('-created_at')

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

def about(request):
    return render(request, 'pages/about.html')

def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if request.user != comment.user:
        messages.error(request, "You can't edit this comment.")
        return redirect(comment.post.get_absolute_url())

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            comment.content = content + (" (edited)")
            comment.save()
            messages.success(request, "Comment updated.")
        return redirect(comment.post.get_absolute_url())

def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.user != comment.user:
        messages.error(request, "You can't delete this comment.")
        return redirect(comment.post.get_absolute_url())

    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
        return redirect(comment.post.get_absolute_url())
    comment = get_object_or_404(Comment, pk=pk)

    # Only allow the comment owner to delete
    if comment.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    if request.method == 'POST':
        post_url = comment.post.get_absolute_url()
        comment.delete()
        return redirect(post_url)

    return render(request, 'blog/delete_comment.html', {'comment': comment})