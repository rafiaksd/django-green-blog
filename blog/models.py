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

from PIL import Image

from django.urls import reverse

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
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')

    description = models.TextField(blank=True, help_text="short blog description")

    content = RichTextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    publish = models.BooleanField(default=False)

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
                    print(f"💀 OLD BLOG IMAGE NOT being USED, DELETING: {old_image_path}")
                    original.image.delete(save=False)
                else:
                    posts_using_old_image = BlogPost.objects.filter(image=old_image_path).exclude(pk=self.pk)
                    print(f"OLD BLOG IMAGE is BEING USED by: {[post.title for post in posts_using_old_image]}")
            

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

        # after everything updated, 
        # now check wether self.image is greater than 1 mb

        try:
            if self.image:
                img_path = self.image.path
                img = Image.open(img_path)

                # Check image size in bytes
                if self.image.size > 1024 * 1024:  # 1 MB
                    # Resize proportionally
                    max_width = 1200  # optional: max width to avoid huge images
                    max_height = 1200

                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Save back, overwrite original
                    img.save(img_path, optimize=True, quality=70)

                    print(f"📷✅😮 BLOG IMAGE: {img_path} resized properly")
                else:
                    print(f"📷 BLOG Image: {img_path} is under 1MB, no resizing needed")
        except Exception as e:
            print(f"FAILED to RESIZE BLOG IMAGE: {img_path}, reason: {e}")

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'id': self.id, 'slug': self.slug})
    
    def __str__(self):
        return self.title


# Signal to delete image file when BlogPost is deleted
@receiver(post_delete, sender=BlogPost)
def delete_blog_image(sender, instance, **kwargs):
    try:
        if instance.image: #if the blog has a main_image
            if os.path.isfile(instance.image.path):
                print(f"🏀💥🗑️ IMAGE {instance.image.path}: DELETED as BLOG is DELETED")
                os.remove(instance.image.path)

        # --- Handle CKEditor images ---
        unused_images_in_CKEDITOR = set(get_images_from_content(instance.content))

        if len(unused_images_in_CKEDITOR) > 0:
            for img in unused_images_in_CKEDITOR:
                full_path = os.path.join(settings.MEDIA_ROOT, img)
                if os.path.exists(full_path):
                    print(f"💀💥🗑️ AFTER DELETE BLOG: CKEditor image not used, deleting: {img}")
                    os.remove(full_path)
        else:
            print(f"0️⃣0️⃣0️⃣ There are NO IMAGES LEFT in CKEDITOR")
        
    except Exception as e:
        print(f"ERROR trying to DELETE unused photos, after deleting blog, due to: {e}")

class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'
