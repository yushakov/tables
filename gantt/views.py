from django.shortcuts import render
from rest_framework import viewsets
from list.models import Choice  # Import Choice model from MyApp
from .serializers import ChoiceSerializer
from django.contrib.auth.decorators import login_required

class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChoiceSerializer

    def get_queryset(self):
        queryset = Choice.objects.all()[:10]
        construct_id = int(self.request.GET.get('id', '-1'))
        if construct_id >= 0:
            queryset = Choice.objects.filter(construct__id=construct_id)  # Adjust the filter to match your model's relation
        return queryset


# Create your views here.

@login_required
def index(request, construct_id):
    return render(request, 'gantt/index.html', {'construct_id': construct_id})
