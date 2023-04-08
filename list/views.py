from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from .models import Construct, Choice
import json
from urllib.parse import unquote_plus
from datetime import datetime

class IndexView(generic.ListView):
    template_name = 'list/index.html'
    context_object_name = 'active_construct_list'

    def get_queryset(self):
        """Return the projects"""
        return Construct.objects.order_by('overall_progress_percent_num')


def index(request):
    constructs = Construct.objects.order_by('overall_progress_percent_num')
    price, price_vat, profit, paid, tobe_paid_for_progress = 0.0, 0.0, 0.0, 0.0, 0.0
    for construct in constructs:
        price += sum([choice.price_num * choice.quantity_num for choice in construct.choice_set.all()])
    context = {'active_construct_list': constructs,
               'price': price,
               'price_vat': price * (1. + construct.vat_percent_num * 0.01),
              }
    print('We are Here, in Index function')
    return render(request, 'list/index.html', context)
    

def update_choice(choice_id, cell_data):
    # can't be a header
    print(f'Choice ID: {choice_id}')
    print(cell_data)
    if cell_data['class'] == 'Choice':
        cells = cell_data['cells']
        choice = Choice.objects.get(pk=choice_id)
        if cells['class'] == 'delete':
            print(f'DELETE "{choice.name_txt}" from "{choice.construct}"')
            print(choice.__dict__)
            choice.delete()
        else:
            print(f'UPDATE "{choice.name_txt}" from "{choice.construct}"')
            choice.name_txt = cells['name']
            choice.notes_txt = ''
            choice.quantity_num = cells['quantity']
            choice.units_of_measure_text = cells['units']
            choice.price_num = cells['price'].replace('£','').replace(',','').strip()
            choice.progress_percent_num = cells['progress'].replace('%','').strip()
            choice.plan_start_date = datetime.strptime(cells['day_start'], "%B %d, %Y").strftime("%Y-%m-%d")
            choice.plan_days_num = cells['days']
            choice.save()
    return choice_id


def create_choice(cell_data, construct):
    # can be just header
    print(f'Construct ID: {construct.id}')
    print(cell_data)
    if cell_data['class'] == 'Choice':
        cells = cell_data['cells']
        if cells['class'] == 'delete': return -1
        choice = Choice(construct=construct,
             name_txt = cells['name'],
             notes_txt = '',
             quantity_num = cells['quantity'],
             units_of_measure_text = cells['units'],
             price_num = cells['price'].replace('£','').replace(',','').strip(),
             progress_percent_num = cells['progress'].replace('%','').strip(),
             plan_start_date = cells['day_start'],
             plan_days_num = cells['days'])
        choice.save()
        print(f'new choice ID: {choice.id}')
        return choice.id
    elif cell_data['class'].startswith('Header'):
        print('Creating header')
    return -1


def save_update(data, construct):
    for key in data.keys():
        row_id = data[key]['id']
        if row_id.startswith('tr_'):
            choice_id = update_choice(row_id.replace('tr_',''), data[key])
        else:
            choice_id = create_choice(data[key], construct)


def detail(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    if request.method == 'POST' and request.POST["json_value"]:
        data = json.loads(request.POST["json_value"])
        save_update(data, construct)
        #for key in data.keys():
            #print(f'{key}:')
            #print(data[key])
    ch_list = []
    construct_total_price = 0.0
    construct_progress = 0.0
    for idx, choice in enumerate(construct.choice_set.all()):
        choice_price = choice.price_num * choice.quantity_num
        construct_progress += choice_price * 0.01 * choice.progress_percent_num
        construct_total_price += choice_price
        ch_list.append({'idx': idx+1, 'choice': choice, 'choice_total_price': choice_price})
    if construct_total_price > 0.0:
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

