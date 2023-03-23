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
    for choice in construct.choice_set.all():
        choice_price = choice.price_num * choice.quantity_num
        construct_progress += choice_price * 0.01 * choice.progress_percent_num
        construct_total_price += choice_price
        ch_list.append({'choice': choice, 'choice_total_price': choice_price})
    construct_progress *= 100. / construct_total_price 
    construct.overall_progress_percent_num = construct_progress
    construct.save()
    form_tags = [{'show0':f'show{i}', 'show1':f'show{i+1}', 'f0':f'f{i}', 'display':'block' if i == 0 else 'none'}
                for i in range(5)]
    context = {'construct': construct,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'construct_total_vat': construct_total_price * (1. + 0.01*construct.vat_percent_num),
               'form_tags': form_tags}
    return render(request, 'list/detail.html', context)

