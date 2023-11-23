from django.urls import path
from . import views
from django.shortcuts import redirect

app_name = 'gantt'
urlpatterns = [
    # path('', views.IndexView.as_view(), name='index'),
    path('', views.index, name='index'),
]
