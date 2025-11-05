from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User

# auto delete image if blog deleted
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

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
        # Auto-generate slug based on the title
        if not self.slug:
            self.slug = slugify(self.title)
        
        # If title is updated, regenerate the slug
        if self.pk:
            original = BlogPost.objects.get(pk=self.pk)
            if original.title != self.title:
                self.slug = slugify(self.title)

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
