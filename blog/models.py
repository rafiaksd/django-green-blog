from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User

# auto delete image -- main ImageField
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

# auto delete image -- CKEditor images
from django.conf import settings
import re
from urllib.parse import urlparse

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided or if the name has changed
        if self.pk:  # Check if the object already exists (update)
            original = Category.objects.get(pk=self.pk)
            if original.name != self.name:  # If the name has changed, regenerate the slug
                self.slug = slugify(self.name)
        elif not self.slug:  # If slug is not provided, generate it from the name
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided or if the name has changed
        if self.pk:  # Check if the object already exists (update)
            original = Tag.objects.get(pk=self.pk)
            if original.name != self.name:  # If the name has changed, regenerate the slug
                self.slug = slugify(self.name)
        elif not self.slug:  # If slug is not provided, generate it from the name
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

def get_images_from_content(html_content):
    """Extract list of image paths from CKEditor HTML content."""
    if not html_content:
        return []

    # Find all src attributes of img tags
    img_urls = re.findall(r'<img [^>]*src="([^"]+)"', html_content)
    img_paths = []

    for url in img_urls:
        # Convert URL to MEDIA_ROOT path if it's local
        parsed = urlparse(url)
        if not parsed.netloc:  # relative URL
            # Remove MEDIA_URL prefix to get relative path
            relative_path = url.replace(settings.MEDIA_URL, "")
            img_paths.append(relative_path)
    return img_paths

class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')
    content = RichTextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if self.pk:
            original = BlogPost.objects.get(pk=self.pk)
            if original.title != self.title:
                self.slug = slugify(self.title)

            # Handle main ImageField
            old_image_path = original.image.name if original.image else None
            new_image_path = self.image.name if self.image else None

            if old_image_path and old_image_path != new_image_path:
                if not BlogPost.objects.filter(image=old_image_path).exclude(pk=self.pk).exists():
                    print(f"💀 OLD IMAGE NOT being USED, DELETING: {old_image_path}")
                    original.image.delete(save=False)
                else:
                    posts_using_old_image = BlogPost.objects.filter(image=old_image_path).exclude(pk=self.pk)
                    print(f"OLD IMAGE is BEING USED by: {[post.title for post in posts_using_old_image]}")

            # --- Handle CKEditor images ---
            old_images = set(get_images_from_content(original.content))
            new_images = set(get_images_from_content(self.content))
            removed_images = old_images - new_images

            for img in removed_images:
                # Check if any other post still uses this image
                still_used = BlogPost.objects.exclude(pk=self.pk).filter(content__icontains=img).exists()
                if not still_used:
                    full_path = os.path.join(settings.MEDIA_ROOT, img)
                    if os.path.exists(full_path):
                        print(f"💀 CKEditor image not used, deleting: {img}")
                        os.remove(full_path)

        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.title


# Signal to delete image file when BlogPost is deleted
@receiver(post_delete, sender=BlogPost)
def delete_blog_image(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'
