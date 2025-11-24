# recommend/urls.py
from django.urls import path
from .views import main, llm_endpoint, status_endpoint

urlpatterns = [
    path("", main, name="main"),
    path("api/llm/", llm_endpoint, name="llm_endpoint"),
    path("api/status/", status_endpoint, name="status_endpoint"),
]
