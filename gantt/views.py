from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from list.models import Choice, Construct
from .serializers import TaskSerializer
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
import json
from copy import deepcopy as copy

class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        # TODO: refactor carefully
        # TODO: write tests
        # TODO: fix the BUG: two consequtive headers on the top break the chart
        queryset = []
        if not self.request.user.is_authenticated:
            get_object_or_404(Construct, pk=-1)
        construct_id = int(self.request.GET.get('id', '-1'))
        if construct_id >= 0:
            construct = Construct.objects.get(pk=construct_id)
            choices = Choice.objects.filter(construct__id=construct_id).order_by('plan_start_date')
            project_struct = json.loads(construct.struct_json)
            group_id = construct.title_text
            project = {'id': group_id,
                    'construct_name': '',
                    'name_txt': group_id,
                    'plan_start_date': timezone.now().date(),
                    'plan_days_num': 1,
                    'type': 'project',
                    'progress_percent_num': 0,
                    'hide_children': 0,
                    'display_order': 0}
            queryset.append(copy(project))
            dates = []
            tmp_set = []
            for key, val in project_struct.items():
                if val['type'].find('Choice') >= 0:
                    choice = choices.filter(id=val['id'])[0]
                    task = TaskSerializer.transform_choice_to_task(choice)
                    task['construct_name'] = group_id
                    task['display_order'] = int(key.replace('line_', ''))
                    tmp_set.append(task)
                    dates.append([task['plan_start_date'], task['plan_days_num']])
                else:
                    queryset += sorted(tmp_set, key=lambda x: x['plan_start_date'])
                    tmp_set = []
                    group_id = val['id']
                    project['id'] = project['name_txt'] = group_id
                    project['display_order'] = int(key.replace('line_', ''))
                    queryset.append(copy(project))
            queryset += sorted(tmp_set, key=lambda x: x['plan_start_date'])
            out = []
            for i, q in enumerate(queryset):
                q['display_order'] = i + 1
                out.append(q)
        return out


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
