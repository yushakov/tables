from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from list.models import Choice, Construct
from .serializers import TaskSerializer
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone

class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = []
        if not self.request.user.is_authenticated:
            get_object_or_404(Construct, pk=-1)
        construct_id = int(self.request.GET.get('id', '-1'))
        if construct_id >= 0:
            construct = Construct.objects.get(pk=construct_id)
            choices = Choice.objects.filter(construct__id=construct_id).order_by('plan_start_date')
            queryset = [TaskSerializer.transform_choice_to_task(choice) for choice in choices]
            project = {'id': construct.title_text,
                    'construct_name': '',
                    'name_txt': construct.title_text,
                    'plan_start_date': timezone.now().date(),
                    'plan_days_num': 1,
                    'type': 'project',
                    'progress_percent_num': 0,
                    'hide_children': 0,
                    'display_order': 1}
            queryset = [project] + queryset
        return queryset


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
