from django.shortcuts import render
from rest_framework import viewsets
from list.models import Choice  # Import Choice model from MyApp
from .serializers import ChoiceSerializer
from django.contrib.auth.decorators import login_required

class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Choice.objects.filter(construct__title_text__icontains='gantt')
    serializer_class = ChoiceSerializer


# Create your views here.

@login_required
def index(request):
    return render(request, 'gantt/index.html', {})
