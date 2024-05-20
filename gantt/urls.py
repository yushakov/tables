from django.urls import path, include
from . import views
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter
from .views import ChoiceViewSet, SlugChoiceViewSet, ConstructsViewSet

router = DefaultRouter()
router.register(r'choices', ChoiceViewSet, basename='choice')
router.register(r'slug_choices', SlugChoiceViewSet, basename='choice')
router.register(r'constructs', ConstructsViewSet, basename='choice')

app_name = 'gantt'
urlpatterns = [
    path('<int:construct_id>', views.index, name='index'),
    path('slug/<str:slug>', views.slug, name='slug'),
    path('constructs/', views.constructs, name='constructs'),
    path('api/', include(router.urls)),
    path('api/choices_update/', views.choices_update, name='choices_update'),
]
