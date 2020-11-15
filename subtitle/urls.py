from django.urls import path
from .views import SearchSubtitle as Search

urlpatterns = [
    path('', Search.as_view(), name='search-subtitle'),
]
