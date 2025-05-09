# blog/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('tentang/', views.about, name='about'),
    path('explore/', views.explore, name='explore'),
]
