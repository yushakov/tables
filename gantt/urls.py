from django.urls import path, include
from . import views
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from .views import ChoiceViewSet

router = DefaultRouter()
router.register(r'choices', ChoiceViewSet, basename='choice')

app_name = 'gantt'
urlpatterns = [
    path('<int:construct_id>', views.index, name='index'),
    path('api/', include(router.urls)),
]
