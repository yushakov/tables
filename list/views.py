from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from .models import Construct, Choice, Invoice, Transaction, HistoryRecord, getConstructAndMaxId
from .models import User
from .models import Category, CLIENT_GROUP_NAME, WORKER_GROUP_NAME
from .forms import TransactionSubmitForm
from .forms import InvoiceSubmitForm
import json
import re
from urllib.parse import unquote_plus
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import logging
from django.contrib.auth.decorators import login_required,\
                                           permission_required, \
                                           user_passes_test
from django.utils import timezone
from django import forms
from django.conf import settings
import os
import shutil

logger = logging.getLogger('django')

class IndexView(generic.ListView):
    template_name = 'list/index.html'
    context_object_name = 'active_construct_list'

    def get_queryset(self):
        """Return the projects"""
        return Construct.objects.order_by('overall_progress_percent_num')

def fix_category(constructs, categories):
    if len(categories) > 0:
        for con in constructs:
            if len(con.category_set.all()) == 0:
                logger.warning(f"Put '{con}' into category '{categories[0].name}'")
                con.category_set.add(categories[0].id)

def get_total(constructs):
    total = {}
    full_cost = 0
    full_cost_vat = 0
    vat_from_income = 0
    full_progress_cost = 0
    round_income = 0
    round_outcome = 0
    round_expenses = 0
    round_salaries = 0
    company_profit = 0
    owner_profit = 0
    salaries_part = 0
    left_to_pay = 0
    invoices_to_pay = 0
    invoices_pending_pay = 0
    for con in constructs:
        full_cost += con.full_cost
        full_cost_vat += con.full_cost_vat
        vat_from_income += con.vat_from_income
        full_progress_cost += con.full_progress_cost
        round_income += con.round_income
        round_outcome += con.round_outcome
        round_expenses += con.round_expenses
        round_salaries += con.round_salaries
        company_profit += con.company_profit
        owner_profit += con.owner_profit
        salaries_part += con.salaries_part
        left_to_pay += con.left_to_pay
        invoices_to_pay += con.invoices_to_pay
        invoices_pending_pay += con.invoices_pending_pay
    total['invoices_pending_pay'] = invoices_pending_pay
    total['invoices_to_pay'] = invoices_to_pay
    total['left_to_pay'] = left_to_pay
    total['salaries_part'] = salaries_part
    total['owner_profit'] = owner_profit
    total['company_profit'] = company_profit
    total['round_salaries'] = round_salaries
    total['round_expenses'] = round_expenses
    total['round_income'] = round_income
    total['round_outcome'] = round_outcome
    total['full_cost'] = full_cost
    total['full_cost_vat'] = full_cost_vat
    total['vat_from_income'] = vat_from_income
    total['full_progress_cost'] = full_progress_cost
    total['overall_progress_percent_num'] = 0.0
    if full_cost > 1.e-4:
        total['overall_progress_percent_num'] = full_progress_cost / full_cost * 100.0
    return total


def get_client_ip_address(request):
    req_headers = request.META
    x_forwarded_for_value = req_headers.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for_value:
        ip_addr = x_forwarded_for_value.split(',')[-1].strip()
    else:
        ip_addr = req_headers.get('REMOTE_ADDR')
    return ip_addr


@login_required
@user_passes_test(lambda user: user.is_staff)
def backup(request):
    db_file = settings.BASE_DIR / 'db.sqlite3'
    backup_folder = settings.BASE_DIR / 'backups'
    new_file_name = 'Can not access db or folder.'
    if os.access(db_file, os.F_OK) and os.access(backup_folder, os.F_OK):
        try:
            now = timezone.now()
            # no often than every hour
            time_suffix = now.strftime('%Y_%m_%d_around_%H_oclock')
            new_file_name = 'db_' + time_suffix + '.sqlite3'
            dst = backup_folder / new_file_name
            if os.access(dst, os.F_OK):
                new_file_name = 'File already exists.'
            else:
                shutil.copy(db_file, dst)
                new_file_name = f'File copied: {new_file_name}.'
        except:
            new_file_name = 'Error copying db file'
    ip = get_client_ip_address(request)
    whatever = f"Backup at {timezone.now()}, {new_file_name}"
    logger.info(f"*action* backup() by '{request.user.username}'. Info: {whatever}. --::-- {ip}")
    return render(request, 'list/account.html', {'whatever': whatever})


@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
def index(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: index() by {request.user.username} --::-- ip: {ip}')
    all_constructs = Construct.objects.all()
    all_cats = Category.objects.order_by('priority')
    fix_category(all_constructs, all_cats)
    cats = all_cats
    ctg_id = [0]
    try:
        ctg_id = [int(c) for c in request.GET.get('category', '0').split(',')]
    except:
        pass
    if ctg_id[0] > 0:
        cats = []
        for cid in ctg_id:
            try:
                cat = all_cats.get(id=cid)
                cats.append(cat)
            except:
                pass
    adi = ''
    try:
        adi += str(all_cats.filter(name__icontains='active')[0].id) + ','
        adi += str(all_cats.filter(name__icontains='done')[0].id)
    except:
        pass
    constructs = []
    for ctg in cats:
        cons = all_constructs.filter(category=ctg.id)
        for con in cons:
            con.color = ctg.color
            constructs.append(con)
    foreman = int(request.GET.get('foreman', '-1'))
    if foreman > 0:
        constructs = [con for con in constructs if con.foreman is not None and con.foreman.id == foreman]
    total = get_total(constructs)
    context = {'active_construct_list': constructs,
               'categories': all_cats,
               'active_done_inds': adi,
               'noscale': True,
               'total': total
              }
    return render(request, 'list/index.html', context)

def get_active_done_constructs():
    cats = Category.objects.all()
    active, done = [], []
    active_cats = cats.filter(name__icontains='active')
    done_cats = cats.filter(name__icontains='done')
    if len(active_cats) > 0:
        for ac in active_cats:
            active += [con for con in ac.constructs.all()]
    if len(done_cats) > 0:
        for dc in done_cats:
            done += [con for con in dc.constructs.all()]
    return active + done

def get_user_invoices(user):
    invoices = user.invoice_set.all()
    unpaid = [inv for inv in invoices.filter(status=Invoice.UNPAID)]
    paid = [inv for inv in invoices.filter(status=Invoice.PAID)]
    return unpaid + paid

@login_required
def account(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: account() by {request.user.username}, {ip}')
    groups = request.user.groups.all()
    slugs = []
    for constr in request.user.accessible_constructs.all():
        slugs.append({'url': constr.slug_name,
                      'project_name': constr.title_text,
                      'id': constr.id})
    constructs = get_active_done_constructs()
    invoices = get_user_invoices(request.user)
    foreman_constructs = [con for con in constructs if con.foreman and con.foreman.id == request.user.id]
    context = {'user': request.user,
               'groups': groups,
               'project_slugs': slugs,
               'is_client': len(groups.filter(name=CLIENT_GROUP_NAME)) > 0,
               'is_worker': len(groups.filter(name=WORKER_GROUP_NAME)) > 0,
               'foreman_constructs': foreman_constructs,
               'constructs': constructs,
               'invoices': invoices
              }
    return render(request, 'list/account.html', context)

def is_yyyy_mm_dd(date_field):
    try:
        datetime.strptime(date_field, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_dd_mm_yyyy(date_field):
    try:
        datetime.strptime(date_field, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def is_month_day_year(date_field):
    try:
        datetime.strptime(date_field, "%B %d, %Y")
        return True
    except ValueError:
        return False


def is_abbrev_month_dot_day_year(date_field):
    try:
        datetime.strptime(date_field, "%b. %d, %Y")
        return True
    except ValueError:
        return False


def is_abbrev_month_day_year(date_field):
    try:
        datetime.strptime(date_field, "%b %d, %Y")
        return True
    except ValueError:
        return False


def format_date(date_str):
    if is_month_day_year(date_str):
        return datetime.strptime(date_str, "%B %d, %Y").date()
    elif is_abbrev_month_day_year(date_str):
        return datetime.strptime(date_str, "%b %d, %Y").date()
    elif is_abbrev_month_dot_day_year(date_str):
        return datetime.strptime(date_str, "%b. %d, %Y").date()
    elif is_yyyy_mm_dd(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    elif is_dd_mm_yyyy(date_str):
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    else:
        raise Exception(f"Unknown date format: {date_str}")


def prepare_data(cells):
    data = dict()
    data['name_txt'] = cells['name']
    data['notes_txt'] = ''
    data['quantity_num'] = float(cells['quantity'].replace(',','').strip())
    data['units_of_measure_text'] = cells['units']
    data['price_num'] = float(cells['price'].replace('£','').replace(',','').strip())
    data['workers'] = str(cells['assigned_to'])
    data['progress_percent_num'] = float(cells['progress'].replace('%','').strip())
    data['main_contract_choice'] = False
    try:
        data['plan_start_date'] = format_date(cells['day_start'])
    except Exception as e:
        logger.error(f"Start date error for '{cells['name']}': {e}")
        data['plan_start_date'] = timezone.now().date()
    data['plan_days_num'] = float(cells['days'])
    data['constructive_notes'] = ""
    data['client_notes'] = ""
    if 'notes' in cells.keys():
        data['constructive_notes'] = cells['notes']['constructive_notes']
        data['client_notes'] = cells['notes']['client_notes']
        data['main_contract_choice'] = data['constructive_notes'].find('#main') >= 0
    return data

def update_choice(choice_id, cell_data, client=False):
    # can be a header
    if type(choice_id) != int:
        try:
            choice_id = int(str(choice_id).replace(',', '').strip())
        except:
            choice_id = -1
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
            choice.main_contract_choice =     data['main_contract_choice']
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
             client_notes          = data['client_notes'],
             main_contract_choice  = data['main_contract_choice'])
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
    construct.struct_json = string_structure
    construct.save()


def __add_choice_to_structure(structure, choice):
    lines = [int(k.split('_')[1]) for k in structure.keys()]
    lines.sort()
    max_num = lines[-1] + 1
    structure[f'line_{max_num}'] = {'type':'Choice', 'id':str(choice.id)}


def _add_missing_choices(structure, choices):
    structure_ids = [int(structure[k]['id']) for k in structure.keys() if structure[k]['type'].startswith('Choice')]
    structure_ids.sort()
    choice_ids = [(ch.id, ch) for ch in choices]
    choice_ids.sort(key=lambda x: x[0])
    for ch_id, ch in choice_ids:
        if ch_id in structure_ids: continue
        __add_choice_to_structure(structure, ch)


def _remove_nonexisting_choices(structure, choices):
    keys_to_remove = []
    choice_ids = [int(ch.id) for ch in choices]
    for k in structure.keys():
        if not structure[k]['type'].startswith('Choice'): continue
        ch_id = int(structure[k]['id'])
        if ch_id not in choice_ids:
            keys_to_remove.append(k)
    for k in keys_to_remove:
        structure.pop(k)


def _order_structure_lines(structure):
    new_struct = {}
    for i, k in enumerate(structure.keys()):
        new_struct[f'line_{i+1}'] = structure[k]
    return new_struct


def fix_structure(structure, choices):
    _add_missing_choices(structure, choices)
    _remove_nonexisting_choices(structure, choices)
    return _order_structure_lines(structure)


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
    logger.critical(f'ERROR: Integrity mismatch')
    logger.critical(f'Choices: {choice_ids}')
    logger.critical(f'Structure: {ids_in_struct}')
    return fix_structure(struc, choices)


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
        self.main_contract_choice = False


def getChoiceListAndPrices(struc_dict, choice_dict):
    ch_list = []
    construct_total_price = 0.0
    construct_total_price2 = 0.0
    construct_total_price3 = 0.0
    construct_progress = 0.0
    choice, choice_price = None, None
    price_prft_vat = None
    price_prft = None
    for idx, line_x in enumerate(struc_dict.values()):
        item_price_prft_vat = None
        item_price_prft = None
        if line_x['type'].startswith('Choice'):
            choice = choice_dict[line_x['id']]
            choice_price = choice.price_num * choice.quantity_num
            construct_progress += choice_price * 0.01 * choice.progress_percent_num
            construct_total_price += choice_price
            prcnt_coeff_profit = ((1. + 0.01 * choice.construct.company_profit_percent_num)
                               *  (1. + 0.01 * choice.construct.ontop_profit_percent_num))
            prcnt_coeff_profit_vat = (prcnt_coeff_profit
                                   *  (1. + 0.01 * choice.construct.vat_percent_num))
            item_price_prft = choice.price_num * prcnt_coeff_profit
            item_price_prft_vat = choice.price_num * prcnt_coeff_profit_vat
            price_prft_vat = choice_price * prcnt_coeff_profit_vat
            price_prft = choice_price * prcnt_coeff_profit
            construct_total_price2 += price_prft_vat
            construct_total_price3 += price_prft
        else:
            choice = FakeChoice(idx, line_x['id'])
        main_contract = ''
        if choice.main_contract_choice:
            main_contract = 'main-contract'
        ch_list.append({'idx': idx+1, 'type': line_x['type'], 'choice': choice,
                        'choice_total_price': choice_price,
                        'item_price_prft_vat': item_price_prft_vat,
                        'item_price_prft': item_price_prft,
                        'price_prft_vat': price_prft_vat,
                        'price_prft': price_prft,
                        'main_contract': main_contract})
    return (ch_list, construct_progress,
            construct_total_price, construct_total_price2,
            construct_total_price3)


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
        logger.debug('POST data in detail():\n %s', request.POST["json_value"])
        if checkTimeStamp(data, construct):
            save_update(data, construct, client)


def get_history_records(construct, limit=8):
    records = construct.get_history_records(limit)
    history = []
    if len(records) > 1:
        history = [{'rec1':records[i+1], 'rec2':records[i]} for i in range(len(records)-1)]
    return history


def extend_session(request):
    one_day_seconds = 60 * 60 * 24
    if request.session.get_expiry_date() < (timezone.now() + timedelta(days=1)):
        request.session.set_expiry(one_day_seconds)


@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
def bg_process_post(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: bg_process_post({construct.title_text}) by {request.user.username}, {ip}')
    if request.method == 'POST':
        process_post(request, construct)
        construct.history_dump(request.user.id)
    extend_session(request)
    data = {
        'message': 'The construct has been updated.',
        'newToken': 'goes here (TBD)'
    }
    return JsonResponse(data)


@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
def detail(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: detail({construct.title_text}) by {request.user.username}, {ip}')
    if request.method == 'POST':
        process_post(request, construct)
        construct.history_dump(request.user.id)
    extend_session(request)
    struc_dict, choice_dict = getStructChoiceDict(construct)
    (ch_list, construct_progress, construct_total_price,
     _, _) = getChoiceListAndPrices(struc_dict, choice_dict)
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price 
    if construct.overall_progress_percent_num != construct_progress:
        construct.overall_progress_percent_num = construct_progress
        construct.save()
    total_and_profit = construct_total_price * (1. + 0.01 * construct.company_profit_percent_num)
    profit = construct_total_price * 0.01 * construct.company_profit_percent_num
    on_top_profit = total_and_profit * 0.01 * construct.ontop_profit_percent_num
    on_top_profit_and_vat = (total_and_profit + on_top_profit) * 0.01 * construct.vat_percent_num
    history = get_history_records(construct)
    session_expiration = request.session.get_expiry_date()
    context = {'construct': construct,
               'session_expiration': f"{session_expiration.strftime('%H:%M, %d.%m.%Y')}",
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'total_and_profit': total_and_profit,
               'total_profit_vat': total_and_profit * (1. + 0.01 * construct.vat_percent_num),
               'on_top_profit': on_top_profit,
               'on_top_profit_and_vat': on_top_profit_and_vat,
               'total_total': (construct_total_price + profit + on_top_profit) * (1. + 0.01 * construct.vat_percent_num),
               'construct_paid': round(construct.income()),
               'noscale': True,
               'history': history}
    return render(request, 'list/detail.html', context)


@login_required
def actions(request):
    actions = []
    with open('logs/info.log', 'r') as f:
        for line in f:
            if line.find("*action*") >= 0:
                actions.append({'line': line.replace("*action*", "")
                                            .replace("Transaction", "<b>Transaction</b>")
                                            .replace("Invoice", "<b>Invoice</b>")
                                            .replace("client", "<b>client</b>")
                                            .replace("Client", "<b>Client</b>")
                                            .replace("Choice", "<b>Choice</b>")
                                            .replace("choice", "<b>choice</b>")
                                            .replace("INFO", "")
                                            })
    actions = actions[::-1]
    actions = actions[:500]
    context = {'actions': actions}
    return render(request, 'list/actions.html', context)


def client_or_worker(user):
    if user.is_staff:
        return True
    groups = user.groups.all()
    if len(groups.filter(name=CLIENT_GROUP_NAME)) > 0 or \
            len(groups.filter(name=WORKER_GROUP_NAME)) > 0:
        return True
    return False


@login_required
@user_passes_test(client_or_worker)
def client(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: client({construct.title_text}) by {request.user.username}, {ip}')
    is_foreman = (request.user.id == construct.foreman.id) if construct.foreman else False
    is_client = len(request.user.groups.filter(name=CLIENT_GROUP_NAME)) > 0
    has_access = len(request.user.accessible_constructs.filter(id=construct.id)) > 0
    if is_client and not has_access:
        return redirect('list:account')
    if request.method == 'POST' and not is_foreman:
        process_post(request, construct, client=True)
        construct.history_dump(request.user.id)
        logger.info(f'*action* client submission for {construct.title_text} by {request.user.username}')
    extend_session(request)
    struc_dict, choice_dict = getStructChoiceDict(construct)
    (ch_list, construct_progress, construct_total_price,
     _, _) = getChoiceListAndPrices(struc_dict, choice_dict)
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price 
    if construct.overall_progress_percent_num != construct_progress:
        construct.overall_progress_percent_num = construct_progress
        construct.save()
    total_and_profit = construct_total_price * (1. + 0.01*construct.company_profit_percent_num)
    is_worker = not (is_foreman or is_client)
    logger.info(f'*action* client({construct.title_text}) by {request.user.username} as worker ({is_worker}), foreman ({is_foreman}), client ({is_client}), has access ({has_access}), {ip}')
    context = {'construct': construct,
               'is_foreman': is_foreman,
               'is_client': is_client,
               'has_access': has_access,
               'is_worker': is_worker,
               'ch_list': ch_list,
               'construct_total': construct_total_price,
               'total_and_profit': total_and_profit,
               'total_profit_vat': total_and_profit * (1. + 0.01*construct.vat_percent_num),
               'noscale': True,
               'construct_paid': construct.income()}
    return render(request, 'list/client_view.html', context)


def client_slug(request, slug, version=1):
    construct = Construct.objects.filter(slug_name=slug).first()
    if construct is None:
        raise Http404("Project not found")
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: client({construct.title_text}) with slug: {slug}, {ip}')
    if request.method == 'POST':
        process_post(request, construct, client=True)
        construct.history_dump(-1)
        logger.info(f"*action* client (slug) submission for construct '{construct.title_text}'.")
    struc_dict, choice_dict = getStructChoiceDict(construct)
    (ch_list,
     construct_progress,
     construct_total_price,
     total_price2, total_price3) = getChoiceListAndPrices(struc_dict, choice_dict)
    if construct_total_price > 0.0:
        construct_progress *= 100. / construct_total_price
    if construct.overall_progress_percent_num != construct_progress:
        construct.overall_progress_percent_num = construct_progress
        construct.save()
    total_and_profit = construct_total_price * (1. + 0.01*construct.company_profit_percent_num)
    deposit = construct.expected_deposit
    if construct.deposit > 0.0:
        deposit = construct.deposit
    logos = get_logos("constructive_choice_partner_logos")
    context = {'construct': construct,
               'deposit': deposit,
               'ch_list': ch_list,
               'is_client': True,
               'has_access': True,
               'construct_total': construct_total_price,
               'construct_total2': total_price2,
               'construct_total3': total_price3,
               'total_and_profit': total_and_profit,
               'total_profit_vat': total_and_profit * (1. + 0.01*construct.vat_percent_num),
               'noscale': True,
               'construct_paid': construct.income(),
               'logos': logos}
    if version == 1:
        return render(request, 'list/client_view.html', context)
    if version == 2:
        return render(request, 'list/client2_view.html', context)


def client2_slug(request, slug):
    return client_slug(request, slug, version=2)


def client_slug_bg_update(request, slug, version=1):
    construct = Construct.objects.filter(slug_name=slug).first()
    if construct is None:
        raise Http404("Project not found")
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: client_slug_bg_update({construct.title_text}), {ip}')
    if request.method == 'POST':
        process_post(request, construct, client=True)
        construct.history_dump(-1)
    data = {
        'message': 'Notes have been updated.',
        'newToken': 'No tokens for slug.'
    }
    return JsonResponse(data)


@login_required
@permission_required("list.add_construct")
@permission_required("list.change_construct")
def clone_construct(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    logger.info(f'*action* USER ACCESS: clone_construct({construct.title_text}) by {request.user.username}')
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
@permission_required("list.change_construct")
def gantt(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    logger.info(f'*action* USER ACCESS: gantt({construct.title_text}) by {request.user.username}')
    struc_dict, choice_dict = getStructChoiceDict(construct)
    ch_list, _, _, _, _, _ = getChoiceListAndPrices(struc_dict, choice_dict)
    common_start, marking, total, labels = getMarking(ch_list)
    context = {'construct': construct, 'ch_list': ch_list, 'start': common_start.strftime('%B'),
               'marking': json.dumps(marking), 'total': total, 'labels': labels}
    return render(request, 'list/gantt.html', context)


def getTransactions(invoice):
    out = list()
    total = 0
    if invoice.status == 'Paid':
        transactions = invoice.transactions.all()
        for tra in transactions:
            tra_dict = dict()
            tra_dict['id']     = tra.id
            tra_dict['number'] = tra.receipt_number
            tra_dict['from']   = tra.from_txt
            tra_dict['amount'] = str(tra.amount)
            total += float(tra.amount)
            out.append(tra_dict)
    return out, total


def get_printed_invoice_lines(details, amount=0):
    lines = details.split('\n')
    out = []
    for line_num, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        fields = [f.strip() for f in line.split(',')]
        time_now = datetime.now().strftime('%d.%m.%Y')
        item = {'quantity': 1, 'description': f'Work done by {time_now}.',
                'unit_price': amount, 'amount': amount, 'class': 'even-line'}
        if len(fields) >= 1: item['quantity'] = fields[0]
        if len(fields) >= 2: item['description'] = fields[1]
        if len(fields) >= 3: item['unit_price'] = fields[2]
        if len(fields) >= 4: item['amount'] = fields[3]
        if line_num % 2 == 1:
            item['class'] = 'odd-line'
        out.append(item)
    return out


def get_number(line):
    line2 = str(line).strip().replace(',', '')
    mtch = re.search( '([0-9\.]+)', line2)
    number = 0.0
    try:
        number = float(mtch[0])
    except:
        number = 0.0
    return number


def process_invoice_lines(lines, price_coeff=1.0):
    total_amount = 0.0
    for line in lines:
        quantity = get_number(line['quantity'])
        unit_price = price_coeff * get_number(line['unit_price'])
        line['unit_price'] = unit_price
        amount = quantity * unit_price
        line['amount'] = amount
        total_amount += amount
    return lines, total_amount


def get_logos(folder):
    img_dir = os.path.join(settings.STATIC_ROOT, "images", folder)
    logos = [os.path.join(folder, f) for f in os.listdir(img_dir)]
    return logos


@login_required
@permission_required("list.view_invoice")
def print_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    logger.info(f'*action* USER ACCESS: print_invoice({invoice.id}) by {request.user.username}')
    invoice_amount = float(invoice.amount)
    vat_prc = float(invoice.construct.vat_percent_num)
    vat_exclude_coeff = 1.0 / (vat_prc * 0.01 + 1.0)
    lines = get_printed_invoice_lines(invoice.details_txt, invoice.amount)
    lines, lines_amount = process_invoice_lines(lines, vat_exclude_coeff)
    vat_from_total = lines_amount * 0.01 * vat_prc
    total_and_vat = lines_amount + vat_from_total
    warning = ''
    if abs(invoice_amount - total_and_vat) > 0.01:
        warning = f"Actual invoice amount (£{invoice_amount}) " + \
                f"is different from the total amount from lines: £{total_and_vat}. " + \
                f"Either your invoice price is wrong, or there is a mistake in the lines."
    user = request.user
    if user.is_staff:
        another_user_id = int(request.GET.get('user_id', -1))
        if another_user_id > 0:
            try:
                user = User.objects.get(pk=another_user_id)
            except:
                logger.error(f"print_invoice(): Cannot get user by user id '{another_user_id}'")
                user = request.user
    logos = get_logos("constructive_choice_partner_logos")
    context = {'user': user,
               'invoice': invoice,
               'no_logout_link': True,
               'lines': lines,
               'lines_amount': lines_amount,
               'warning': warning,
               'vat_from_total': vat_from_total,
               'total_and_vat': total_and_vat,
               'logos': logos}
    return render(request, 'list/print_invoice.html', context)


@login_required
@permission_required("list.view_invoice")
def get_invoice_fields(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    logger.info(f'*action* USER ACCESS: get_invoice_fields({construct.id}) by {request.user.username}')
    choices = construct.choice_set.all()
    choices_modified = []
    for ch in choices:
        choices_modified.append({
            'qty_num': ch.quantity_num,
            'qty_name': ch.units_of_measure_text.replace(",", ";"),
            'name': ch.name_txt.replace(",", ";"),
            'price': str(ch.price_num).replace(",", "")})
    context = {"construct": construct,
               "choices": choices_modified}
    return render(request, 'list/get_invoice_fields.html', context)


@login_required
@permission_required("list.view_invoice")
def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: view_invoice({invoice.id}) by {request.user.username}, {ip}')
    tra_list, tra_total = getTransactions(invoice)
    payment_mismatch = invoice.check_mismatch(save=True)
    user_is_owner = True
    user_invoices = request.user.invoice_set.filter(id=invoice_id)
    if len(user_invoices) == 0:
        user_is_owner = False
    staff_users = []
    if request.user.is_staff:
        staff_users = list(User.objects.filter(is_staff=True))
    context = {'invoice': invoice,
               'transactions': tra_list,
               'pay_more': float(invoice.amount) - tra_total,
               'total_paid': tra_total,
               'mismatch': payment_mismatch,
               'user_is_owner': user_is_owner,
               'username': request.user.username,
               'staff_users': staff_users}
    return render(request, 'list/view_invoice.html', context)


def getInvoices(transaction):
    return transaction.invoice_set.all()


@login_required
@permission_required("list.view_transaction")
def view_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: view_transaction({transaction.id}) by {request.user.username}, {ip}')
    inv_list = getInvoices(transaction)
    invoices = {'len': len(inv_list), 'list': inv_list}
    context = {'transaction': transaction, 'invoices': invoices}
    return render(request, 'list/view_transaction.html', context)


@login_required
@permission_required("list.add_transaction")
@permission_required("list.change_transaction")
def submit_transaction(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: submit_transaction() by {request.user.username}, {ip}')
    if request.method == 'POST':
        form = TransactionSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            obj = Transaction.objects.order_by('id').last()
            return redirect(obj)
    else:
        construct_id = int(request.GET.get('construct', '-1'))
        from_txt = str(request.user.company)
        if request.user.company is None or len(from_txt.strip()) < 3:
            from_txt = str(request.user.first_name).strip() + " " + str(request.user.last_name).strip()
        initial_data = {'construct': construct_id,
                        'invoices': [request.GET.get('invoice', -1)],
                        'amount': request.GET.get('amount','').replace(',',''),
                        'from_txt': request.GET.get('from', from_txt),
                        'to_txt': request.GET.get('to', ''),
                        'transaction_type': request.GET.get('type',''),
                        'receipt_number': getConstructAndMaxId(construct_id, Transaction)
                       }
        form = TransactionSubmitForm(initial = initial_data)
    return render(request, 'list/submit_transaction.html', {'form': form})

@login_required
@permission_required("list.add_transaction")
@permission_required("list.change_transaction")
def submit_transaction_bunch(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: submit_transaction() by {request.user.username}, {ip}')
    lines_to_show = ""
    lines_added = []
    errors = []
    constructs = Construct.objects.all()
    construct_id = int(request.GET.get("construct", -1))
    field_nums = "1,2,3,4,5,6,7"
    delimiter = '\t'
    if request.method == 'POST':
        construct_id = int(request.POST.get('construct_id', -1))
        delimiter_option = request.POST.get('delimiter', "1")
        field_nums = request.POST.get('field_nums', '1,2,3,4,5,6,7')
        lines = request.POST.get('lines', "")
        try:
            construct = Construct.objects.get(id=construct_id)
        except Exception as e:
            errors.append(f"with getting the construct id = {construct_id}.")
            context = {'constructs': constructs, 'lines': lines,
                    'errors': errors, 'field_nums': field_nums}
            return render(request, 'list/submit_transaction_bunch.html', context)
        lines = [line.strip() for line in lines.split("\n")]
        delimiters = {'1': '\t', '2': ','}
        delimiter = delimiters[delimiter_option]
        for i, line in enumerate(lines):
            if len(line.strip()) == 0:
                continue
            fields = [f.strip() for f in line.split(delimiter)]
            try:
                inds = [int(f.strip()) - 1 for f in field_nums.split(',')]
                from_txt = str(fields[inds[0]])
                to_txt   = str(fields[inds[1]])
                amount   = float(fields[inds[2]])
                inout    = str(fields[inds[3]]).upper()
                date     = format_date(str(fields[inds[4]]))
                number   = str(fields[inds[5]])
                details  = str(fields[inds[6]])
                Transaction.add_as_on_page(construct, from_txt, to_txt, amount, inout,
                                           date, number, details)
                lines_added.append(line.strip())
            except Exception as e:
                lines_to_show += line.strip() + "\n"
                errors.append(f"with \"{line.strip()}\" ({e})")
    context_delimiters = [{'value': '1', 'selected': 'selected' if delimiter == '\t' else '', 'name': 'tab'},
                          {'value': '2', 'selected': 'selected' if delimiter == ',' else '', 'name': 'comma'}]
    context = {'constructs': constructs, 'lines': lines_to_show, 'field_nums': field_nums,
            'errors': errors, 'added': lines_added, 'construct_id': construct_id,
            'delimiters': context_delimiters}
    return render(request, 'list/submit_transaction_bunch.html', context)

@login_required
@permission_required("list.add_invoice")
def submit_invoice(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: submit_invoice() by {request.user.username}, {ip}')
    if request.method == 'POST':
        form = InvoiceSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            obj = Invoice.objects.order_by('id').last()
            logger.info(f"*action* Invoice submitted: {obj} for construct: {obj.construct.title_text}")
            return redirect(obj)
    else:
        construct_id = int(request.GET.get('construct', '-1'))
        invoice_type = request.GET.get('type', 'OUT')
        details = request.GET.get('details', '-')
        amount = request.GET.get('amount', '')
        initial_data = {'construct': construct_id,
                        'seller': request.user.first_name + ' ' + request.user.last_name,
                        'owner': request.user.id,
                        'amount': amount,
                        'invoice_type': invoice_type,
                        'number': getConstructAndMaxId(construct_id, Invoice),
                        'details_txt': details}
        form = InvoiceSubmitForm(initial=initial_data)
        hide_owner_label = False
        if not request.user.is_superuser:
            form.fields['owner'].widget = forms.HiddenInput()
            hide_owner_label = True
        if 'worker' in request.GET:
            form.fields['invoice_type'].widget = forms.HiddenInput()
            form.fields['invoice_type'].initial = 'OUT'
            form.fields['status'].widget = forms.HiddenInput()
            form.fields['status'].initial = 'Unpaid'
        context = {'form': form, 'hide_owner_label': hide_owner_label}
    return render(request, 'list/submit_invoice.html', context)

@login_required
@permission_required("list.change_invoice")
def modify_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    logger.info(f'*action* USER ACCESS: modify_invoice({invoice.id}) by {request.user.username}')
    if request.method == 'POST':
        form = InvoiceSubmitForm(request.POST, request.FILES, instance=invoice)
        if form.is_valid():
            form.save()
            obj = Invoice.objects.get(pk=invoice_id)
            return redirect(obj)
    else:
        form = InvoiceSubmitForm(instance=invoice)
        if not request.user.is_superuser:
            form.fields['owner'].widget = forms.HiddenInput()
        # form.fields['photo'].widget = forms.HiddenInput()
        form.fields['number'].widget = forms.HiddenInput()
        form.fields['status'].widget = forms.HiddenInput()
        form.fields['invoice_type'].widget = forms.HiddenInput()
    return render(request, 'list/modify_invoice.html', {'form': form})

@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
def history(request):
    logger.info(f'USER ACCESS: history() by {request.user.username}')
    context = {}
    if request.method == "GET":
        if 'id1' in request.GET and 'id2' in request.GET:
            id1 = int(request.GET['id1'])
            id2 = int(request.GET['id2'])
            context['text'] = HistoryRecord.get_diff(id1, id2)
    return render(request, 'list/history.html', context)

def getTotalAmount(transactions):
    if transactions is None: return 0.0
    total = 0.0
    for tra in transactions:
        total += float(tra.amount)
    return total


@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
@permission_required("list.add_construct")
def flows(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: flows({construct.title_text}) by {request.user.username}, {ip}')
    incoming_transactions = construct.transaction_set.filter(transaction_type=Transaction.INCOMING).order_by('date')
    outgoing_transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING).order_by('date')
    salary_transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING,
            details_txt__icontains='salary').order_by('date')
    incoming_invoices = construct.invoice_set.filter(invoice_type=Transaction.INCOMING).order_by('issue_date')
    incoming_unpaid_invoices = construct.invoice_set.filter(invoice_type=Transaction.INCOMING,
            status=Invoice.UNPAID).order_by('issue_date')
    outgoing_invoices = construct.invoice_set.filter(invoice_type=Transaction.OUTGOING).order_by('issue_date')
    outgoing_unpaid_invoices = construct.invoice_set.filter(invoice_type=Transaction.OUTGOING,
            status=Invoice.UNPAID).order_by('issue_date')
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


@login_required
@permission_required("list.view_construct")
@permission_required("list.change_construct")
@permission_required("list.add_construct")
def transactions(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: transactions({construct.title_text}) by {request.user.username}, {ip}')
    context = {'construct_id': construct.id, 'construct_name': construct.title_text}
    transactions = []
    direction = 'all'
    if request.method == "GET":
        direction = request.GET.get('direction', 'all')
        context['direction'] = direction
        if   direction == 'in':
            transactions = construct.transaction_set.filter(transaction_type=Transaction.INCOMING).order_by('date')
        elif direction == 'out':
            transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING).order_by('date')
        elif direction == 'salary':
            transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING,
                details_txt__icontains='salary').order_by('date')
        elif direction == 'expenses':
            transactions = construct.transaction_set.filter(transaction_type=Transaction.OUTGOING) \
                .exclude(details_txt__icontains='salary').order_by('date')
        else:
            transactions = construct.transaction_set.all()
    total = round(sum([tra.amount for tra in transactions]))
    context['transactions'] = transactions
    context['total'] = total
    return render(request, 'list/all_transactions.html', context)


@login_required
@user_passes_test(lambda user: user.is_superuser)
def invoices(request, construct_id):
    construct = get_object_or_404(Construct, pk=construct_id)
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: invoices({construct.title_text}) by {request.user.username}, {ip}')
    context = {'construct_id': construct.id, 'construct_name': construct.title_text}
    invoices = []
    direction = 'all'
    if request.method == "GET":
        direction = request.GET.get('direction', 'all')
        context['direction'] = direction
        if   direction == 'in':
            invoices = construct.invoice_set.filter(invoice_type=Transaction.INCOMING).order_by('issue_date')
        elif direction == 'out':
            invoices = construct.invoice_set.filter(invoice_type=Transaction.OUTGOING).order_by('issue_date')
        elif direction == 'unpaid':
            invoices = construct.invoice_set.filter(status=Invoice.UNPAID).order_by('issue_date')
        elif direction == 'mismatch':
            invoices = construct.invoice_set.all()
            for inv in invoices:
                inv.check_mismatch(save=True)
            invoices = construct.invoice_set.filter(payment_mismatch=True).order_by('issue_date')
        else:
            invoices = construct.invoice_set.all()
    total = round(sum([inv.amount for inv in invoices]))
    context['invoices'] = invoices
    context['total'] = total
    return render(request, 'list/all_invoices.html', context)


@login_required
@user_passes_test(lambda user: user.is_superuser)
def invoices_payall(request):
    ip = get_client_ip_address(request)
    logger.info(f'*action* USER ACCESS: invoices_payall() by {request.user.username}, {ip}')
    new_transactions = []
    if request.method == 'POST':
        invoice_user_ids = [k.replace('box_', '') for k in request.POST.keys() if k.startswith('box_')]
        user_dict = {}
        for uid_iid in invoice_user_ids:
            user_id, inv_id = uid_iid.split('_')
            if user_id in user_dict:
                user_dict[user_id].append(inv_id)
            else:
                user_dict[user_id] = [inv_id]
        amounts = {}
        for uid, invoice_ids in user_dict.items():
            user = User.objects.get(pk=int(uid))
            amounts = {invoice_id: float(request.POST['full_amount_' + invoice_id].replace(',', '')) for invoice_id in invoice_ids}
            user_total = sum(amounts.values())
            for invoice_id in invoice_ids:
                invoice = Invoice.objects.get(pk=invoice_id)
                if invoice.status == Invoice.PAID:
                    continue
                construct_id = invoice.construct.id
                receipt_number = getConstructAndMaxId(construct_id, Transaction)
                date = timezone.now().strftime("%Y-%m-%d")
                transaction = Transaction(construct=invoice.construct,
                                          from_txt="Constructive Choice Ltd",  # request.user.company,
                                          to_txt=user.first_name + user.last_name,
                                          amount=amounts[invoice_id],
                                          transaction_type=Transaction.OUTGOING,
                                          date=date,
                                          receipt_number=receipt_number,
                                          details_txt=invoice.details_txt + '\n' + \
                                                      "#partof " + str(user_total) + \
                                                      ", " + date)
                transaction.save()
                invoice.status = Invoice.PAID
                invoice.transactions.add(transaction)
                invoice.save()
                invtra = transaction.invoicetransaction_set.last()
                invtra.construct = invoice.construct
                invtra.save()
                new_transactions.append(f"{transaction.receipt_number}, " +
                                        f"{transaction.from_txt} -> " +
                                        f"{transaction.to_txt}, " +
                                        f"£ {transaction.amount}, " +
                                        f"//{transaction.details_txt}// " +
                                        f"[[ {transaction.construct.title_text} ]]")
    invoices = []
    context = {'new_transactions': new_transactions, 'cis_percent': Invoice.cis_percent}
    direction = 'sort_by_user'
    context['direction'] = direction
    invoices = Invoice.objects.filter(status=Invoice.UNPAID).filter(invoice_type=Transaction.OUTGOING)
    if direction == 'sort_by_user':
        users = [inv.owner for inv in invoices]
        users = sorted(list(set(users)), key=lambda u: u.first_name + u.last_name + u.username)
        subsets = []
        for user in users:
            subset = {'user': user}
            subset['invoices'] = []
            for inv in invoices:
                if inv.owner.id != user.id:
                    continue
                subset_invoice = {'issue_date': inv.issue_date,
                                    'due_date': inv.due_date,
                                    'number': inv.number,
                                    'amount': float(inv.amount),
                                    'was_amount': float(inv.amount),
                                    'cis_amount': 0,
                                    'status': inv.status,
                                    'id': inv.id,
                                    'details_txt': inv.details_txt,
                                    'construct': inv.construct}
                if inv.details_txt.find('#materials') < 0:
                    subset_invoice['amount'] *= 1. - Invoice.cis_percent * 0.01
                    subset_invoice['cis_amount'] = subset_invoice['was_amount'] - subset_invoice['amount']
                subset['invoices'].append(subset_invoice)
            subset['amount'] = round(sum([inv['amount'] for inv in subset['invoices']]))
            subset['total'] = round(sum([inv['was_amount'] for inv in subset['invoices']]))
            subset['cis'] = round(sum([float(inv['was_amount']) - float(inv['amount']) for inv in subset['invoices']]))
            subsets.append(subset)
    total = round(sum([s['amount'] for s in subsets]))
    context['subsets'] = subsets
    context['total'] = total
    return render(request, 'list/invoices_payall.html', context)
