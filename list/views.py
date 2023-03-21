from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from .models import Construct

class IndexView(generic.ListView):
    template_name = 'list/index.html'
    context_object_name = 'active_construct_list'

    def get_queryset(self):
        """Return the projects"""
        return Construct.objects.order_by('overall_progress_percent_num')

def detail(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    context = {'construct': construct}
    return render(request, 'list/detail.html', context)

