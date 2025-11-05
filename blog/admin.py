from django.contrib import admin
from django import forms
from .models import BlogPost, Category, Tag, Comment
from ckeditor.widgets import CKEditorWidget


# BlogPostForm to exclude slug from being manually edited
class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = BlogPost
        fields = '__all__'
        exclude = ['author'] #inteded author for now is ONLY ONE, so IGNORING FOR NOW
        #exclude = ['slug']


# BlogPostAdmin with the custom BlogPostForm
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogPostForm
    list_display = ('title', 'category', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('category', 'tags')
    #readonly_fields = ('slug',)  # Make slug field read-only


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
