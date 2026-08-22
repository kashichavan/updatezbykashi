from django.urls import path
from .views import blog_list_view, blog_detail_view, blog_create_view, api_blog_like_view

app_name = 'blog'

urlpatterns = [
    path('', blog_list_view, name='blog_list'),
    path('manage/new/', blog_create_view, name='blog_create'),
    path('write/', blog_create_view, name='blog_write'),
    path('<slug:slug>/like/', api_blog_like_view, name='blog_like'),
    path('<slug:slug>/', blog_detail_view, name='blog_detail'),
]


