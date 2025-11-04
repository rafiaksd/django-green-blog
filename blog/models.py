from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User

# image resizing
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

# auto delete image if blog deleted
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    content = RichTextField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title)

        # First save to ensure image is available
        super().save(*args, **kwargs)

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
        except Exception as e:
            # If resizing fails, delete the uploaded image file
            if os.path.exists(img_path):
                os.remove(img_path)
            # Clear image field so broken file isn't saved
            self.image = None
            super().save(update_fields=['image'])
            # Raise or log the exception as needed
            raise e

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
