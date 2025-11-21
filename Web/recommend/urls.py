# recommend/urls.py
from django.urls import path
from .views import main

urlpatterns = [
    path("", main, name="main"),  # 템플릿에서 {% url 'main' %} 쓰고 있어서 name='main'
]
