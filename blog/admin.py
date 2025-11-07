from django.contrib import admin, messages
from django.conf import settings
from django import forms
from .models import BlogPost, Category, Tag, Comment, get_images_from_content
from ckeditor.widgets import CKEditorWidget
import os
from django.urls import path
from django.shortcuts import redirect

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'email_preview', 'created_at', 'content')

    def email_preview(self, obj):
        return obj.user.email

# BlogPostForm to exclude slug from being manually edited
class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = BlogPost
        fields = '__all__'
        exclude = ['author','slug']
        # exclude = ['slug']

# BlogPostAdmin with the custom BlogPostForm
class BlogPostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
    form = BlogPostForm
    list_display = ('title', 'category', 'publish', 'created_at', 'updated_at')
    list_editable = ('publish',)  # make publish editable right in the list
    list_filter = ('category', 'tags', 'publish')
    search_fields = ('title', 'category__name', 'content')
    #readonly_fields = ('slug',)  # Make slug field read-only

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('delete-unused-images/', self.admin_site.admin_view(self.delete_unused_images_view), name='delete_unused_images'),
        ]
        return custom_urls + urls
    
    def delete_unused_images_view(self, request):
        deleted_images_count = 0
        all_posts = BlogPost.objects.all()
        used_images = set()
        media_root = settings.MEDIA_ROOT

        # --- Collect all used image paths ---
        for post in all_posts:
            # Main image (ImageField)
            if post.image:
                try:
                    rel_path = os.path.relpath(post.image.path, media_root)
                    used_images.add(rel_path.replace("\\", "/"))  # normalize slashes
                except Exception as e:
                    print(f"⚠️ Could not resolve main image path for {post.title}: {e}")

            # CKEditor images (from content)
            content_images = get_images_from_content(post.content)
            for img in content_images:
                # remove leading slash and normalize
                clean_img = img.lstrip("/").replace("\\", "/")
                used_images.add(clean_img)

        print(f"🧩 Total used images detected: {len(used_images)}")
        print(f"Sample used images: {list(used_images)[:5]}")

        # --- Scan blog_images/ folder for unused files ---
        blog_images_folder = os.path.join(media_root, "blog_images")
        if not os.path.exists(blog_images_folder):
            self.message_user(request, "❌ blog_images folder does not exist.", level=messages.ERROR)
            return redirect('..')

        scanned_images = 0
        for root, dirs, files in os.walk(blog_images_folder):
            for file in files:
                scanned_images += 1
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, media_root).replace("\\", "/")

                if rel_path not in used_images:
                    try:
                        os.remove(file_path)
                        deleted_images_count += 1
                        print(f"💀 Deleted unused image: {rel_path}")
                    except Exception as e:
                        print(f"⚠️ Failed to delete {rel_path}: {e}")
                else:
                    print(f"✅ Keeping in use: {rel_path}")
                

        self.message_user(
            request,
            f"✅ Scan complete. Scanned {scanned_images} images, Deleted {deleted_images_count} unused images.",
            level=messages.SUCCESS
        )

        return redirect('..')
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['delete_unused_images_url'] = 'admin:delete_unused_images'
        return super().changelist_view(request, extra_context=extra_context)

# CategoryForm to prevent slug field from being edited
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        exclude = ['slug']  # Exclude slug from form, it will be auto-generated

# CategoryAdmin with the custom CategoryForm
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('name', 'slug')  # Show name and auto-generated slug
    readonly_fields = ('slug',)  # Make slug field read-only


# TagForm to prevent slug field from being edited
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = '__all__'
        exclude = ['slug']  # Exclude slug from form, it will be auto-generated

# TagAdmin with the custom TagForm
class TagAdmin(admin.ModelAdmin):
    form = TagForm
    list_display = ('name', 'slug')  # Show name and auto-generated slug
    readonly_fields = ('slug',)  # Make slug field read-only


# Register your models
admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment)

# Customize admin site headers and titles
admin.site.site_header = "Client Blog Dashboard"
admin.site.site_title = "Blog Admin"
admin.site.index_title = "Manage Blog Content"

# forces the "View site" link to /greenblog/
admin.site.site_url = '/greenblog/'