from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import generic
from .models import Construct, Choice
import json
from urllib.parse import unquote_plus
from datetime import datetime
from django.core.exceptions import ValidationError

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
    return render(request, 'list/index.html', context)
    

def update_choice(choice_id, cell_data):
    # can be a header
    if cell_data['class'] == 'Choice':
        cells = cell_data['cells']
        choice = Choice.objects.get(pk=choice_id)
        if cells['class'] == 'delete':
            print(f'DELETE "{choice.name_txt}" (id: {choice.id}) from "{choice.construct}"')
            print(choice.__dict__)
            choice.delete()
            return -1
        else:
            print(f'UPDATE "{choice.name_txt[:50]}" (id: {choice.id}) from "{choice.construct}"')
            choice.name_txt = cells['name']
            choice.notes_txt = ''
            choice.quantity_num = float(cells['quantity'].strip())
            choice.units_of_measure_text = cells['units']
            choice.price_num = float(cells['price'].replace('£','').replace(',','').strip())
            choice.progress_percent_num = float(cells['progress'].replace('%','').strip())
            choice.plan_start_date = datetime.strptime(cells['day_start'], "%B %d, %Y").date()
            choice.plan_days_num = float(cells['days'])
            choice.save()
            return int(choice_id)
        return -1
    return -1


def create_choice(cell_data, construct):
    if cell_data['class'] == 'Choice':
        cells = cell_data['cells']
        # if it's new, but already deleted
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
        return choice.id
    # can be just header
    return -1


def add_to_structure(structure, row_data, choice_id):
    ln_cntr = len(structure) + 1
    row_type = row_data['class']
    row_id = None
    if row_type.startswith('Header'):
        if row_data['cells']['class'].find('delete') >= 0: return
        if row_data['cells']['name'].find('£') >= 0:
            row_id = row_data['cells']['name'].split('£')[0].strip()
        else:
            row_id = row_data['cells']['name'].strip()
    else:
        if choice_id < 0: return
        row_id = str(choice_id)
    structure.update({f'line_{ln_cntr}':{'type':row_type, 'id':row_id}})


def save_update(data, construct):
    structure = dict()
    ln_cntr = 1
    for key in data.keys():
        row_id = data[key]['id']
        choice_id = None
        if row_id.startswith('tr_'):
            choice_id = update_choice(row_id.replace('tr_',''), data[key])
        else:
            choice_id = create_choice(data[key], construct)
        add_to_structure(structure, data[key], choice_id)
    string_structure = json.dumps(structure)
    print('Project structure:\n', string_structure)
    construct.struct_json = string_structure
    construct.save()


def check_integrity(structure_str, choices):
    choice_ids = [ch.id for ch in choices]
    struc = {}
    if len(structure_str.strip()) > 0 and \
       len(structure_str.replace('{','').replace('}','').strip()) > 0:
        struc = json.loads(structure_str)
    else:
        struc = {f'line{k+1}': {'type':'Choice', 'id': str(n)} for k, n in enumerate(choice_ids)}
    ids_in_struct = [int(ln['id']) for ln in struc.values() if ln['type'] == 'Choice']
    choice_ids.sort()
    ids_in_struct.sort()
    if choice_ids == ids_in_struct:
        return struc
    return dict()


class FakeChoice:
    def __init__(self, ID, name):
        self.id = ID
        self.name_txt = name


def detail(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    if request.method == 'POST' and request.POST["json_value"]:
        data = json.loads(request.POST["json_value"])
        print(datetime.now(), 'POST data in detail():\n', data)
        save_update(data, construct)
    structure_str = construct.struct_json
    choices = construct.choice_set.all()
    struc_dict = check_integrity(structure_str, choices)
    if(len(choices) > 0 and len(struc_dict) == 0):
        raise ValidationError(f"JSON structure does not correspond to choices of {construct}",
                                code="Bad integrity")
    else:
        print(f'Integrity Ok: {construct}')
    ch_list = []
    construct_total_price = 0.0
    construct_progress = 0.0
    choice, choice_price = None, None
    choice_dict = {str(ch.id):ch for ch in choices}
    for idx, line_x in enumerate(struc_dict.values()):
        if line_x['type'] == 'Choice':
            choice = choice_dict[line_x['id']]
            choice_price = choice.price_num * choice.quantity_num
            construct_progress += choice_price * 0.01 * choice.progress_percent_num
            construct_total_price += choice_price
        else:
            choice = FakeChoice(idx, line_x['id'])
        ch_list.append({'idx': idx+1, 'type': line_x['type'], 'choice': choice, 'choice_total_price': choice_price})
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price 
    construct.overall_progress_percent_num = construct_progress
    construct.save()
    context = {'construct': construct,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'construct_total_vat': construct_total_price * (1. + 0.01*construct.vat_percent_num)}
    return render(request, 'list/detail.html', context)

