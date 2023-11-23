from django.urls import path, include
from . import views
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from .views import ChoiceViewSet

router = DefaultRouter()
router.register(r'choices', ChoiceViewSet)

app_name = 'gantt'
urlpatterns = [
    # path('', views.IndexView.as_view(), name='index'),
    path('', views.index, name='index'),
    path('api/', include(router.urls)),
]
