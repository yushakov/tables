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
    ch_list = []
    construct_total_price = 0.0
    construct_progress = 0.0
    total_working_days = 0
    for choice in construct.choice_set.all():
        total_working_days += choice.plan_days_num
        construct_progress += choice.plan_days_num * 0.01 * choice.progress_percent_num
        choice_price = choice.price_num * choice.quantity_num
        construct_total_price += choice_price
        ch_list.append({'choice': choice, 'choice_total_price': choice_price})
    construct_progress *= 100. / total_working_days
    print(f'total days: {total_working_days}')
    construct.overall_progress_percent_num = construct_progress
    construct.save()
    context = {'construct': construct,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'construct_total_vat': construct_total_price * (1. + 0.01*construct.vat_percent_num)}
    return render(request, 'list/detail.html', context)

