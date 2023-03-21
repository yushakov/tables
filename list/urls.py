from django.urls import path

from . import views

app_name = 'list'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:construct_id>/', views.detail, name='detail')
]
