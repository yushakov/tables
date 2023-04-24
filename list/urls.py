from django.urls import path

from . import views

app_name = 'list'
urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path('', views.index, name='index'),
    path('<int:construct_id>/', views.detail, name='detail'),
    path('<int:construct_id>/gantt/', views.gantt, name='gantt')
]
