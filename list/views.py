from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from .models import Construct, Choice, Invoice, Transaction
from .forms import TransactionSubmitForm
from .forms import InvoiceSubmitForm
import json
from urllib.parse import unquote_plus
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import logging
from django.contrib.auth.decorators import login_required, permission_required

logger = logging.getLogger(__name__)

class IndexView(generic.ListView):
    template_name = 'list/index.html'
    context_object_name = 'active_construct_list'

    def get_queryset(self):
        """Return the projects"""
        return Construct.objects.order_by('overall_progress_percent_num')

@login_required
@permission_required("list.view_construct")
def index(request):
    constructs = Construct.objects.order_by('-listed_date')
    price, price_vat, profit, paid, tobe_paid_for_progress = 0.0, 0.0, 0.0, 0.0, 0.0
    for construct in constructs:
        price += sum([choice.price_num * choice.quantity_num for choice in construct.choice_set.all()])
    context = {'active_construct_list': constructs,
               'price': price,
               'price_vat': price * (1. + construct.vat_percent_num * 0.01),
              }
    return render(request, 'list/index.html', context)
    
def is_yyyy_mm_dd(date_field):
    try:
        datetime.strptime(date_field, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_month_day_year(date_field):
    try:
        datetime.strptime(date_field, "%B %d, %Y")
        return True
    except ValueError:
        return False


def prepare_data(cells):
    data = dict()
    data['name_txt'] = cells['name']
    data['notes_txt'] = ''
    data['quantity_num'] = float(cells['quantity'].strip())
    data['units_of_measure_text'] = cells['units']
    data['price_num'] = float(cells['price'].replace('£','').replace(',','').strip())
    data['workers'] = str(cells['assigned_to'])
    data['progress_percent_num'] = float(cells['progress'].replace('%','').strip())
    if is_month_day_year(cells['day_start']):
        data['plan_start_date'] = datetime.strptime(cells['day_start'], "%B %d, %Y").date()
    elif is_yyyy_mm_dd(cells['day_start']):
        data['plan_start_date'] = datetime.strptime(cells['day_start'], "%Y-%m-%d").date()
    data['plan_days_num'] = float(cells['days'])
    data['constructive_notes'] = ""
    data['client_notes'] = ""
    if 'notes' in cells.keys():
        data['constructive_notes'] = cells['notes']['constructive_notes']
        data['client_notes'] = cells['notes']['client_notes']
    return data

def update_choice(choice_id, cell_data, client=False):
    # can be a header
    if cell_data['class'].find('Choice') >= 0:
        cells = cell_data['cells']
        try:
            choice = Choice.objects.get(pk=choice_id)
        except Exception:
            logger.error(f"EXCEPTION on trying to update choice: {choice_id}")
            logger.error(f"cell_data['cells']: {cells}")
            return -2
        if cells['class'].find('delete') >= 0:
            logger.info(f'DELETE "{choice.name_txt}" (id: {choice.id}) from "{choice.construct}"')
            logger.info(choice.__dict__)
            choice.delete()
            return -1
        else:
            logger.info(f'UPDATE "{choice.name_txt[:50]}" (id: {choice.id}) from "{choice.construct}"')
            data = prepare_data(cells)
            if client:
                choice.client_notes = data['client_notes']
                choice.save()
                return int(choice_id)
            choice.name_txt =                 data['name_txt']
            choice.notes_txt =                data['notes_txt']
            choice.quantity_num =             data['quantity_num']
            choice.units_of_measure_text =    data['units_of_measure_text']
            choice.price_num =                data['price_num']
            choice.workers =                  data['workers']
            choice.progress_percent_num =     data['progress_percent_num']
            choice.plan_start_date =          data['plan_start_date']
            choice.plan_days_num =            data['plan_days_num']          
            choice.constructive_notes =       data['constructive_notes']
            choice.client_notes =             data['client_notes']
            choice.save()
            return int(choice_id)
        return -1
    return -1


def create_choice(cell_data, construct):
    if cell_data['class'].find('Choice') >= 0:
        cells = cell_data['cells']
        # if it's new, but already deleted
        if cells['class'].find('delete') >= 0: return -1
        data = prepare_data(cells)
        choice = Choice(construct=construct,
             name_txt              = data['name_txt'],
             notes_txt             = data['notes_txt'],
             quantity_num          = data['quantity_num'],
             units_of_measure_text = data['units_of_measure_text'],
             price_num             = data['price_num'],
             workers               = data['workers'],
             progress_percent_num  = data['progress_percent_num'],
             plan_start_date       = data['plan_start_date'],
             plan_days_num         = data['plan_days_num'],
             constructive_notes    = data['constructive_notes'],
             client_notes          = data['client_notes'])
        choice.save()
        return choice.id
    # can be just header
    return -1


def add_to_structure(structure, row_data, choice_id, client=False):
    ln_cntr = len(structure) + 1
    row_type = row_data['class']
    row_id = None
    if row_type.startswith('Header'):
        if row_data['cells']['class'].find('delete') >= 0: return
        if row_data['cells']['name'].find('£') >= 0:
            row_id = row_data['cells']['name'].split('£')[0].strip()
        else:
            row_id = row_data['cells']['name'].strip()
    elif row_type.startswith('Choice'):
        row_type = "Choice";
        if choice_id < 0: return
        row_id = str(choice_id)
    structure.update({f'line_{ln_cntr}':{'type':row_type, 'id':row_id}})


def create_or_update_choice(row_id, row, construct, client=False):
    if row_id.startswith('tr_'):
        return update_choice(row_id.replace('tr_',''), row, client)
    elif not client:
        return create_choice(row, construct)
    return -1


def save_update(data, construct, client=False):
    structure = dict()
    client_try_to_change_structure = client
    for key in data.keys():
        if not key.startswith("row_"): continue
        row_id = data[key]['id']
        choice_id = create_or_update_choice(row_id, data[key], construct, client)
        add_to_structure(structure, data[key], choice_id, client)
    if client_try_to_change_structure: return
    string_structure = json.dumps(structure)
    logger.info('Project structure:\n', string_structure)
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
    ids_in_struct = [int(ln['id']) for ln in struc.values() if ln['type'].startswith('Choice')]
    choice_ids.sort()
    ids_in_struct.sort()
    if choice_ids == ids_in_struct:
        return struc
    else:
        logger.critical(f'ERROR: Integrity mismatch')
        logger.error(f'Choices: {choice_ids}')
        logger.error(f'Structure: {ids_in_struct}')
        voc = {str(ch.id): ch.name_txt[:30] for ch in choices}
        for ch in choices:
            print(f'{ch.id}: {ch.name_txt[:30]}')
        for k in struc.keys():
            if struc[k]["type"].startswith("Choice"):
                if struc[k]["id"] in voc.keys():
                    print(f'{k}: {struc[k]["id"]} "{voc[struc[k]["id"]]}"')
                else:
                    print(f'There is no {struc[k]["id"]} in choices IDs')
            else:
                print(f'{k}: {struc[k]}')
    return dict()


def getStructChoiceDict(construct):
    structure_str = construct.struct_json
    choices = construct.choice_set.all()
    struc_dict = check_integrity(structure_str, choices)
    if(len(choices) > 0 and len(struc_dict) == 0):
        raise ValidationError(f"JSON structure does not correspond to choices of {construct}",
                                code="Bad integrity")
    else:
        logger.info(f'Integrity Ok: {construct}')
    choice_dict = {str(ch.id):ch for ch in choices}
    return struc_dict, choice_dict


class FakeChoice:
    def __init__(self, ID, name):
        self.id = ID
        self.name_txt = name


def getChoiceListAndPrices(struc_dict, choice_dict):
    ch_list = []
    construct_total_price = 0.0
    construct_progress = 0.0
    choice, choice_price = None, None
    for idx, line_x in enumerate(struc_dict.values()):
        if line_x['type'].startswith('Choice'):
            choice = choice_dict[line_x['id']]
            choice_price = choice.price_num * choice.quantity_num
            construct_progress += choice_price * 0.01 * choice.progress_percent_num
            construct_total_price += choice_price
        else:
            choice = FakeChoice(idx, line_x['id'])
        ch_list.append({'idx': idx+1, 'type': line_x['type'], 'choice': choice, 'choice_total_price': choice_price})
    return ch_list, construct_progress, construct_total_price


def checkTimeStamp(data, construct):
    if 'timestamp' in data:
        if int(data['timestamp']) > int(construct.last_save_date.timestamp()):
            return True
        else:
            logger.warning(f"WARNING: wrong timestamp. Data: {int(data['timestamp'])}, " +
                   f"construct: {int(construct.last_save_date.timestamp())}. " +
                   f"Data is older by {int(construct.last_save_date.timestamp()) - int(data['timestamp'])} seconds. " +
                   "Was it Re-Send?")
    else:
        logger.error("ERROR: no timestamp")
    return False


def process_post(request, construct, client=False):
    if request.POST["json_value"]:
        data = json.loads(request.POST["json_value"])
        logger.debug(datetime.now(), 'POST data in detail():\n', data)
        if checkTimeStamp(data, construct):
            save_update(data, construct, client)


@login_required
@permission_required("list.view_construct")
def detail(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    if request.method == 'POST':
        process_post(request, construct)
    struc_dict, choice_dict = getStructChoiceDict(construct)
    ch_list, construct_progress, construct_total_price = getChoiceListAndPrices(struc_dict, choice_dict)
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price 
    if construct.overall_progress_percent_num != construct_progress:
        construct.overall_progress_percent_num = construct_progress
        construct.save()
    total_and_profit = construct_total_price * (1. + 0.01*construct.company_profit_percent_num)
    context = {'construct': construct,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'total_and_profit': total_and_profit,
               'total_profit_vat': total_and_profit * (1. + 0.01*construct.vat_percent_num),
               'construct_paid': construct.income()}
    return render(request, 'list/detail.html', context)


@login_required
@permission_required("list.view_construct")
def client(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    if request.method == 'POST':
        process_post(request, construct, client=True)
    struc_dict, choice_dict = getStructChoiceDict(construct)
    ch_list, construct_progress, construct_total_price = getChoiceListAndPrices(struc_dict, choice_dict)
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price 
    if construct.overall_progress_percent_num != construct_progress:
        construct.overall_progress_percent_num = construct_progress
        construct.save()
    total_and_profit = construct_total_price * (1. + 0.01*construct.company_profit_percent_num)
    context = {'construct': construct,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'total_and_profit': total_and_profit,
               'total_profit_vat': total_and_profit * (1. + 0.01*construct.vat_percent_num),
               'construct_paid': construct.income()}
    return render(request, 'list/client_view.html', context)


@login_required
@permission_required("list.add_construct")
@permission_required("list.change_construct")
def clone_construct(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    new_name = 'Copy ' + str(datetime.now()) + ' ' + str(construct.title_text)
    new_construct = construct.copy(new_name)
    context = {'next_page': 'list:index',
               'param': f'{new_construct.id}'}
    return render(request, 'list/wait.html', context)


def getMarking(choice_list):
    starts, ends = [], []
    marking = {}
    for choice in choice_list:
        if choice['type'].startswith('Choice'):
            starts.append(choice['choice'].plan_start_date)
            ends.append(choice['choice'].plan_start_date + timedelta(days=choice['choice'].plan_days_num))
            marking[choice['choice'].id] = {'start': starts[-1], 'end': ends[-1]}
    starts.sort()
    ends.sort()
    total = (ends[-1] - starts[0]).days
    common_start = starts[0]
    labels = ', '.join([str((common_start + timedelta(days=i)).day) for i in range(total)])
    for k in marking.keys():
        marking[k]['start'] = (marking[k]['start'] - common_start).days
        marking[k]['end']   = (marking[k]['end']   - common_start).days - 1
    return common_start, marking, total, labels


@login_required
@permission_required("list.view_construct")
def gantt(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    struc_dict, choice_dict = getStructChoiceDict(construct)
    ch_list, _, _ = getChoiceListAndPrices(struc_dict, choice_dict)
    common_start, marking, total, labels = getMarking(ch_list)
    context = {'construct': construct, 'ch_list': ch_list, 'start': common_start.strftime('%B'),
               'marking': json.dumps(marking), 'total': total, 'labels': labels}
    return render(request, 'list/gantt.html', context)


def getTransactions(invoice):
    out = list()
    if invoice.status == 'Paid':
        transactions = invoice.transactions.all()
        for tra in transactions:
            tra_dict = dict()
            tra_dict['id']     = tra.id
            tra_dict['number'] = tra.receipt_number
            tra_dict['from']   = tra.from_txt
            tra_dict['amount'] = str(tra.amount)
            out.append(tra_dict)
    return out


@login_required
@permission_required("list.view_invoice")
def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    tra_list = getTransactions(invoice)
    context = {'invoice': invoice, 'transactions': tra_list}
    return render(request, 'list/view_invoice.html', context)


def getInvoices(transaction):
    return transaction.invoice_set.all()


@login_required
@permission_required("list.view_transaction")
def view_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    inv_list = getInvoices(transaction)
    invoices = {'len': len(inv_list), 'list': inv_list}
    context = {'transaction': transaction, 'invoices': invoices}
    return render(request, 'list/view_transaction.html', context)


@login_required
@permission_required("list.add_transaction")
@permission_required("list.change_transaction")
def submit_transaction(request):
    if request.method == 'POST':
        form = TransactionSubmitForm(request.POST)
        logger.debug("views.py, submit_transaction()")
        logger.debug(request.POST['photo'])
        if form.is_valid():
            form.save()
            obj = Transaction.objects.latest()
            return redirect(obj)
    else:
        form = TransactionSubmitForm()
    return render(request, 'list/submit_transaction.html', {'form': form})

@login_required
@permission_required("list.add_invoice")
def submit_invoice(request):
    if request.method == 'POST':
        form = InvoiceSubmitForm(request.POST)
        if form.is_valid():
            form.save()
            obj = Invoice.objects.latest()
            return redirect(obj)
    else:
        form = InvoiceSubmitForm()
    return render(request, 'list/submit_invoice.html', {'form': form})

def getTotalAmount(transactions):
    if transactions is None: return 0.0
    total = 0.0
    for tra in transactions:
        total += float(tra.amount)
    return total


@login_required
@permission_required("list.view_construct")
def flows(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    incoming_transactions = construct.transaction_set.filter(transaction_type=Transaction.INCOMING)
    outgoing_transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING)
    salary_transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING,
            details_txt__icontains='salary')
    incoming_invoices = construct.invoice_set.filter(invoice_type=Transaction.INCOMING)
    incoming_unpaid_invoices = construct.invoice_set.filter(invoice_type=Transaction.INCOMING, status=Invoice.UNPAID)
    outgoing_invoices = construct.invoice_set.filter(invoice_type=Transaction.OUTGOING)
    outgoing_unpaid_invoices = construct.invoice_set.filter(invoice_type=Transaction.OUTGOING, status=Invoice.UNPAID)
    context = {'incoming_transactions': incoming_transactions,
            'income': getTotalAmount(incoming_transactions),
            'outgoing_transactions': outgoing_transactions,
            'outcome': getTotalAmount(outgoing_transactions),
            'salary_transactions': salary_transactions,
            'total_salary': getTotalAmount(salary_transactions),
            'incoming_invoices': incoming_invoices,
            'incoming_invoices_total': getTotalAmount(incoming_invoices),
            'incoming_unpaid_invoices': incoming_unpaid_invoices,
            'incoming_unpaid_invoices_total': getTotalAmount(incoming_unpaid_invoices),
            'outgoing_invoices': outgoing_invoices,
            'outgoing_invoices_total': getTotalAmount(outgoing_invoices),
            'outgoing_unpaid_invoices': outgoing_unpaid_invoices,
            'outgoing_unpaid_invoices_total': getTotalAmount(outgoing_unpaid_invoices),
            'construct_id': construct.id,
            'construct_name': construct.title_text}
    return render(request, 'list/flows.html', context)
