from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from list.models import Choice, Construct
from .serializers import ChoiceSerializer
from django.contrib.auth.decorators import login_required
from django.conf import settings

class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChoiceSerializer

    def get_queryset(self):
        queryset = Choice.objects.all()[:1]
        construct_id = int(self.request.GET.get('id', '-1'))
        if construct_id >= 0:
            queryset = Choice.objects.filter(construct__id=construct_id).order_by('plan_start_date')
        return queryset


# Create your views here.

@login_required
def index(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    protocol = settings.PROTOCOL
    host = settings.ALLOWED_HOSTS[0]
    port = settings.PORT
    return render(request, 'gantt/index.html',
                  {'construct_id': construct_id,
                   'title': construct.title_text,
                   'protocol': protocol,
                   'host': host,
                   'port': port
                  })
