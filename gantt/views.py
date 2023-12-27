from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from list.models import Choice, Construct
from .serializers import TaskSerializer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.utils import timezone
import json
from copy import deepcopy as copy
import logging
from list.views import get_client_ip_address

logger = logging.getLogger('django')


def get_formatted_choices(construct_id):
    out, queryset = [], []
    if construct_id >= 0:
        construct = Construct.objects.get(pk=construct_id)
        choices = Choice.objects.filter(construct__id=construct_id).order_by('plan_start_date')
        project_struct = json.loads(construct.struct_json)
        group_id = ''
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
        for i, q in enumerate(queryset):
            q['display_order'] = i + 1
            out.append(q)
    return out


class ChoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # TODO: write tests
        if not self.request.user.is_authenticated:
            get_object_or_404(Construct, pk=-1)
        construct_id = int(self.request.GET.get('id', '-1'))
        return get_formatted_choices(construct_id)


@user_passes_test(lambda user: user.is_staff)
def index(request, construct_id):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: gantt.index(construct.id={construct_id}) by {request.user.username} --::-- ip: {ip}')
    construct = get_object_or_404(Construct, pk=construct_id)
    protocol = settings.PROTOCOL
    host = settings.ALLOWED_HOSTS[0]
    port = settings.PORT
    return render(request, 'gantt/index.html',
                  {'construct_id': construct_id,
                   'title': construct.title_text,
                   'protocol': protocol,
                   'host': host,
                   'port': port,
                   'get_choices_link': ''.join([protocol,
                                                host,
                                                port,
                                                "/gantt/api/choices/?id=",
                                                str(construct_id)]),
                    'interactive': 'true'
                  })


@api_view(['POST'])
@user_passes_test(lambda user: user.is_staff)
def choices_update(request):
    tasks_data = request.data.get('choices')
    for task_data in tasks_data:
        # Validate each task using the serializer
        serializer = TaskSerializer(data=task_data)
        if serializer.is_valid():
            # If valid, manually update the corresponding Choice instance
            task_validated_data = serializer.validated_data
            try:
                choice_id = int(task_validated_data.get('id'))
            except:
                continue
            choice = Choice.objects.get(id=choice_id)
            # Update the Choice instance with the validated data
            choice.plan_start_date = task_validated_data.get('plan_start_date', choice.plan_start_date)
            choice.plan_days_num = task_validated_data.get('plan_days_num', choice.plan_days_num)
            choice.progress_percent_num = int(task_validated_data.get('progress_percent_num', choice.progress_percent_num))
            choice.save()
        else:
            # Handle invalid data
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'status': 'success'}, status=status.HTTP_200_OK)

