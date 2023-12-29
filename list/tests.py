from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.forms.widgets import HiddenInput, Select
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import numpy as np
import re
import datetime as dt
import json
from list.views import check_integrity,   \
                       is_yyyy_mm_dd,     \
                       is_dd_mm_yyyy,     \
                       is_month_day_year, \
                       format_date,       \
                       create_choice,     \
                       update_choice,     \
                       process_post,      \
                       checkTimeStamp,    \
                       fix_structure,     \
                       get_printed_invoice_lines, \
                       get_number,        \
                       process_invoice_lines
from list.models import Construct, \
                        Category, \
                        User, \
                        Choice, \
                        Invoice, \
                        Transaction, \
                        InvoiceTransaction, \
                        HistoryRecord, \
                        getConstructAndMaxId, \
                        dump_all_constructs, \
                        load_all_constructs, \
                        CLIENT_GROUP_NAME, \
                        WORKER_GROUP_NAME
import os


STATUS_CODE_OK = 200
STATUS_CODE_REDIRECT = 302

def get_dummy_image():
    image = Image.new('RGB', (10, 10), color = 'red')
    image_file = io.BytesIO()
    image.save(image_file, format='JPEG')
    image_file.name = 'test_receipt.jpg'
    image_file.seek(0)
    dummy_file = SimpleUploadedFile('test_receipt.jpg', image_file.read(), content_type='image/jpeg')
    return dummy_file

def make_test_choice(construct, name='Some new choice'):
    choice = Choice(construct=construct,
         name_txt              = name,
         notes_txt             = '',
         quantity_num          = 2,
         price_num             = '20.0',
         progress_percent_num  = 25.0,
         units_of_measure_text = 'nr',
         workers               = 'Paul',
         plan_start_date       = '1984-04-15',
         plan_days_num         = 7.0)
    return choice

def make_test_construct(construct_name = 'Some test Construct', user_id=-1, history=False):
    construct = Construct(title_text=construct_name)
    construct.save()
    choice = Choice(construct=construct,
         name_txt              = 'Choice 1',
         notes_txt             = '-',
         constructive_notes    = 'just do it',
         client_notes          = 'yes, lets go',
         quantity_num          = 1,
         price_num             = '10.0',
         progress_percent_num  = 35.0,
         units_of_measure_text = 'nr',
         workers               = 'John',
         plan_start_date       = '1984-04-15',
         plan_days_num         = 5.0)
    choice.save()
    dic = {"line_1": {"type": "Header2", "id": "Some header"}}
    dic["line_2"] = {"type": "Choice", "id": str(choice.id)}
    choice = Choice(construct=construct,
         name_txt              = 'Choice 2',
         notes_txt             = '-',
         constructive_notes    = 'be yourself',
         client_notes          = 'show me',
         quantity_num          = 2,
         price_num             = '20.0',
         progress_percent_num  = 25.0,
         units_of_measure_text = 'nr',
         workers               = 'Paul',
         plan_start_date       = '1984-04-15',
         plan_days_num         = 7.0)
    choice.save()
    dic["line_3"] = {"type": "Choice", "id": str(choice.id)}
    choice = Choice(construct=construct,
         name_txt              = 'Choice 3',
         notes_txt             = '',
         quantity_num          = 2,
         price_num             = '20.0',
         progress_percent_num  = 25.0,
         units_of_measure_text = 'nr',
         workers               = 'Paul',
         plan_start_date       = '1984-04-15',
         plan_days_num         = 7.0)
    choice.save()
    dic["line_4"] = {"type": "Choice", "id": str(choice.id)}
    construct.struct_json = json.dumps(dic)
    construct.save()
    invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
    ta = Transaction.add(construct, 100.0, direction='in')
    ta.invoice_set.add(invoice)
    ta.save()
    inv_tra = ta.invoicetransaction_set.all()
    for intra in inv_tra:
        intra.construct = construct
        intra.save()
    if history:
        fname = construct.history_dump(user_id)
        os.remove(fname)
    return construct


class FunctionTests(TestCase):
    def test_getConstructAndMaxId_negative(self):
        _id = getConstructAndMaxId(-1, Invoice)
        self.assertEqual(_id, '0-0-0')

    def test_getConstructAndMaxId_null(self):
        _id = getConstructAndMaxId(0, Invoice)
        self.assertEqual(_id, '0-0-0')

    def test_getConstructAndMaxId_no_invoices_yet(self):
        construct = Construct()
        construct.save()
        _id = getConstructAndMaxId(construct.id, Invoice)
        self.assertEqual(_id, '1-1-1')

    def test_getConstructAndMaxId_no_transactions_yet(self):
        construct = Construct()
        construct.save()
        _id = getConstructAndMaxId(construct.id, Transaction)
        self.assertEqual(_id, '1-1-1')

    def test_getConstructAndMaxId(self):
        construct = make_test_construct()
        _id = getConstructAndMaxId(construct.id, Invoice)
        self.assertEqual(_id, '1-2-2')

    def test_getConstructAndMaxId_wrong_construct(self):
        construct = make_test_construct()
        _id = getConstructAndMaxId(100, Invoice)
        self.assertEqual(_id, '100-1-2')

    def test_getConstructAndMaxId_global(self):
        construct = make_test_construct()
        _id = getConstructAndMaxId(construct.id, Invoice)
        construct2 = make_test_construct()
        _id2 = getConstructAndMaxId(construct2.id, Invoice)
        self.assertEqual(_id, '1-2-2')
        self.assertEqual(_id2, '2-2-3')


class MyFixChoice:
    def __init__(self):
        self.id = None
    def __str__(self):
        return f'{self.id}'
    def __repr__(self):
        return f'{self.id}'

class StructureFixTests(TestCase):
    def test_fix_structure_missing_choices(self):
        choices = []
        for i in range(1,6):
            ch = MyFixChoice()
            ch.id = i
            choices.append(ch)
        stru = {}
        for i in range(1,4):
            stru[f'line_{i}'] = {'type':'Choice', 'id':str(i)}
        stru = fix_structure(stru, choices)
        stru_ids = [int(stru[k]['id']) for k in stru.keys() if stru[k]['type'].startswith('Choice')]
        choi_ids = [ch.id for ch in choices]
        stru_ids.sort()
        choi_ids.sort()
        self.assertEqual(stru_ids, choi_ids)
        self.assertEqual(len(choices), len(stru.keys()))

    def test_fix_structure_nonexistent_choices(self):
        choices = []
        for i in range(1,4):
            ch = MyFixChoice()
            ch.id = i
            choices.append(ch)
        stru = {}
        for i in range(1,6):
            stru[f'line_{i}'] = {'type':'Choice', 'id':str(i)}
        stru = fix_structure(stru, choices)
        stru_ids = [int(stru[k]['id']) for k in stru.keys() if stru[k]['type'].startswith('Choice')]
        choi_ids = [ch.id for ch in choices]
        stru_ids.sort()
        choi_ids.sort()
        self.assertEqual(stru_ids, choi_ids)
        self.assertEqual(len(choices), len(stru.keys()))

    def test_fix_structure_mix(self):
        choices = []
        for i in [1, 2, 3, 4, 5, 6, 7]:
            ch = MyFixChoice()
            ch.id = i
            choices.append(ch)
        stru = {}
        for i in [1, 8, 3, 4,    6, 7, 9]:
            stru[f'line_{i}'] = {'type':'Choice', 'id':str(i)}
        stru = fix_structure(stru, choices)
        stru_ids = [int(stru[k]['id']) for k in stru.keys() if stru[k]['type'].startswith('Choice')]
        choi_ids = [ch.id for ch in choices]
        stru_ids.sort()
        choi_ids.sort()
        self.assertEqual(stru_ids, choi_ids)
        self.assertEqual(len(choices), len(stru.keys()))

    def _lines_in_order(self, structure):
        lines = [int(k.split('_')[1]) for k in structure.keys()]
        for i in range(1, len(lines)+1):
            if i == lines[i-1]: continue
            return False
        return True

    def test_fix_structure_mix_ordered_lines(self):
        choices = []
        for i in [1, 2, 3, 4, 5, 6, 7]:
            ch = MyFixChoice()
            ch.id = i
            choices.append(ch)
        stru = {}
        for l, i in [(1,1), (2,8), (3,3), (4,4),    (5,6), (6,7), (7,9)]:
            stru[f'line_{l}'] = {'type':'Choice', 'id':str(i)}
        stru = fix_structure(stru, choices)
        stru_ids = [int(stru[k]['id']) for k in stru.keys() if stru[k]['type'].startswith('Choice')]
        choi_ids = [ch.id for ch in choices]
        stru_ids.sort()
        choi_ids.sort()
        self.assertEqual(stru_ids, choi_ids)
        self.assertIs(self._lines_in_order(stru), True)
        self.assertEqual(len(choices), len(stru.keys()))

    def test_fix_structure_big_mix_ordered_lines(self):
        choices = []
        np.random.seed(1)
        ids1 = list(set(list(np.random.choice(list(range(200)), 30))))
        ids2 = list(set(list(np.random.choice(list(range(200)), 30))))
        for i in ids1:
            ch = MyFixChoice()
            ch.id = i
            choices.append(ch)
        stru = {}
        for l, i in enumerate(ids2):
            stru[f'line_{l+1}'] = {'type':'Choice', 'id':str(i)}
        stru = fix_structure(stru, choices)
        stru_ids = [int(stru[k]['id']) for k in stru.keys() if stru[k]['type'].startswith('Choice')]
        choi_ids = [ch.id for ch in choices]
        stru_ids.sort()
        choi_ids.sort()
        self.assertEqual(stru_ids, choi_ids)
        self.assertIs(self._lines_in_order(stru), True)
        self.assertEqual(len(choices), len(stru.keys()))


class HistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='yuran', password='secret', email='yuran@domain.com')
        self.simple_user = User(username='simple', password='secret', email='simple@domain.com')
        self.simple_user.save()
        self.client_user = User.objects.create_user(username='client',
                password='secret',
                email='client@domain.com')
        permission = Permission.objects.get(codename='view_construct')
        self.client_user.user_permissions.add(permission)

    def test_history_dump(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        invoice.transactions.add(ta)
        invoice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        fname = construct.history_dump(self.user.id)
        self.assertIs(os.access(fname, os.F_OK), True)
        os.remove(fname)
        recs = HistoryRecord.objects.all()
        self.assertEqual(len(recs), 1)

    def test_history_dump_unknown_user(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        invoice.transactions.add(ta)
        invoice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        fname = construct.history_dump(-1)
        self.assertIs(os.access(fname, os.F_OK), True)
        os.remove(fname)
        recs = HistoryRecord.objects.all()
        self.assertEqual(len(recs), 1)

    def test_history_records_diff(self):
        construct = make_test_construct()
        fname1 = construct.history_dump(self.user.id)
        choices = construct.choice_set.all()
        choice = choices[0]
        choice.constructive_notes = 'Adding some notes'
        choice.save()
        fname2 = construct.history_dump(self.user.id)
        recs = HistoryRecord.objects.all()
        self.assertEqual(len(recs), 2)
        id1, id2 = recs[1].id, recs[0].id
        diff = HistoryRecord.get_diff(id1, id2)
        self.assertIs(diff.find('Adding some notes') >= 0, True)
        os.remove(fname1)
        os.remove(fname2)

    def test_client_history_records_diff(self):
        construct = make_test_construct()
        fname1 = construct.history_dump(self.client_user.id)
        choices = construct.choice_set.all()
        choice = choices[0]
        choice.client_notes = 'Adding some notes'
        choice.save()
        fname2 = construct.history_dump(self.client_user.id)
        recs = HistoryRecord.objects.all()
        self.assertEqual(len(recs), 2)
        id1, id2 = recs[1].id, recs[0].id
        diff = HistoryRecord.get_diff(id1, id2)
        self.assertIs(diff.find('Adding some notes') >= 0, True)
        os.remove(fname1)
        os.remove(fname2)

    def test_history_records_do_not_mix(self):
        construct1 = make_test_construct('Construct 1')
        construct2 = make_test_construct('Construct 2')
        fname1 = construct1.history_dump(self.user.id)
        fname2 = construct2.history_dump(self.user.id)
        choices = construct1.choice_set.all()
        choice11 = choices[0]
        choice11.name_txt = 'Name1'
        choice11.save()
        choices = construct2.choice_set.all()
        choice22 = choices[0]
        choice22.name_txt = 'Name22'
        choice22.save()
        fname3 = construct1.history_dump(self.user.id)
        fname4 = construct2.history_dump(self.user.id)
        records1 = construct1.get_history_records()
        records2 = construct2.get_history_records()
        tpl1 = tuple(sorted([rec.id for rec in records1]))
        tpl2 = tuple(sorted([rec.id for rec in records2]))
        self.assertEqual(tpl1, (1, 3))
        self.assertEqual(tpl2, (2, 4))
        diff1 = HistoryRecord.get_diff(1, 3)
        diff2 = HistoryRecord.get_diff(2, 4)
        self.assertIs(diff1.find('Name1') >= 0, True)
        self.assertIs(diff2.find('Name22') >= 0, True)
        os.remove(fname1)
        os.remove(fname2)
        os.remove(fname3)
        os.remove(fname4)


    def test_history_records_no_diff_output_for_struct_json(self):
        construct = make_test_construct()
        fname1 = construct.history_dump(self.user.id)
        choices = construct.choice_set.all()
        choice = choices[0]
        choice.constructive_notes = 'Adding some notes'
        choice.save()
        construct.struct_json = construct.struct_json.replace("line_1", "line_11")
        construct.save()
        fname2 = construct.history_dump(self.user.id)
        recs = HistoryRecord.objects.all()
        self.assertEqual(len(recs), 2)
        id1, id2 = recs[1].id, recs[0].id
        diff = HistoryRecord.get_diff(id1, id2)
        self.assertIs(diff.find('Adding some notes') >= 0, True)
        self.assertIs(diff.find('struct_json') < 0, True)
        os.remove(fname1)
        os.remove(fname2)


class ModelTests(TestCase):
    def test_foreman(self):
        foreman = User(username='Foreman')
        foreman.save()
        con = Construct(title_text='construct')
        con.save()
        con.foreman = foreman
        con.save()
        foreman_cons = foreman.foreman_constructs.all()
        self.assertEqual(len(foreman_cons), 1)

    def test_client_user_field(self):
        client = User(username='Client')
        client.save()
        con1 = Construct(title_text='construct1')
        con1.save()
        con1.client_user = client
        con1.save()
        con2 = Construct(title_text='construct2')
        con2.save()
        con2.client_user = client
        con2.save()
        con3 = Construct(title_text='construct3')
        con3.save()
        client_cons = client.client_constructs.all()
        self.assertEqual(len(client_cons), 2)

    def test_categories(self):
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat1.constructs.add(con1.id)
        cat1.constructs.add(con2.id)
        cat2.constructs.add(con3.id)
        cat1.save()
        cat2.save()

    def test_add_category_to_construct(self):
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat2.constructs.add(con2.id)
        cons = Construct.objects.all()
        for con in cons:
            if len(con.category_set.all()) == 0:
                con.category_set.add(cat1.id)
        self.assertEqual(len(cat1.constructs.all()), 2)

    def test_expected_deposit_percent(self):
        import list.models as lm
        construct = Construct(title_text="Deposit holder",
                              vat_percent_num=15.0,
                              company_profit_percent_num=14.0,
                              owner_profit_coeff=0.13)
        construct.save()
        self.assertEqual(construct.deposit_percent_expect, lm.DEPOSIT_PERCENT_EXPECT)

    def test_expected_deposit_percent_2(self):
        import list.models as lm
        construct = Construct(title_text="Deposit holder",
                              vat_percent_num=15.0,
                              company_profit_percent_num=14.0,
                              deposit_percent_expect=20.0,
                              owner_profit_coeff=0.13)
        construct.save()
        self.assertEqual(construct.deposit_percent_expect, 20.0)

    def test_expected_deposit(self):
        import list.models as lm
        construct = Construct(title_text="Deposit holder",
                              vat_percent_num=15.0,
                              company_profit_percent_num=14.0,
                              owner_profit_coeff=0.13)
        construct.save()
        choice1 = Choice(construct=construct,
                         name_txt="Floor",
                         quantity_num = 25.,
                         price_num=1000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice1.save()
        # (work price + VAT + company profit) * 15%
        expected = 25000 * 1.15 * 1.14 * 0.15
        self.assertEqual(construct.expected_deposit, round(expected))

    def test_deposit_main_only(self):
        construct = Construct(title_text="Deposit holder",
                              vat_percent_num=15.0,
                              company_profit_percent_num=14.0,
                              owner_profit_coeff=0.13)
        construct.save()
        choice1 = Choice(construct=construct,
                         name_txt="Floor",
                         quantity_num = 25.,
                         price_num=1000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice1.save()
        choice2 = Choice(construct=construct,
                         name_txt="Walls",
                         quantity_num = 4.,
                         price_num=10000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice2.save()
        choice3 = Choice(construct=construct,
                         name_txt="Roof",
                         quantity_num = 35.,
                         price_num=1000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice3.save()
        def print_it():
            return
            print("         >>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<")
            print(f"Progress: {construct.overall_progress_percent()}%; " +
                  f"Full cost: {construct.full_cost}; " +
                  f"Main cost: {construct.main_cost}; " +
                  f"Paid deposit: {construct.deposit} ({construct.deposit_percent :.2f}%); " +
                  f"Full progress cost: {construct.full_progress_cost};\n" +
                  f"Deposit aware progress cost: {construct.no_deposit_progress_cost} + " +
                  f"{construct.full_side_progress_cost} = " +
                  f"{construct.no_deposit_progress_cost + construct.full_side_progress_cost}; " +
                  f"Income: {construct.round_income}; Outcome: {construct.round_outcome}; " +
                  f"Left to pay: {construct.left_to_pay}")

        def transaction(amo, det):
            # print(f"---------> Transaction: {amo}, {det}")
            ta = Transaction(construct=construct, from_txt="Client", to_txt="Company",
                             amount=amo, details_txt=det,
                             transaction_type="IN")
            ta.save()

        def progress(val):
            # print(f"--------> Progress: {val}%")
            choice1.progress_percent_num = val; choice1.save()
            choice2.progress_percent_num = val; choice2.save()
            choice3.progress_percent_num = val; choice3.save()

        print_it()
        # transaction(construct.main_cost * 0.15, "#deposit")
        transaction(20000, "#deposit")
        self.assertEqual(construct.deposit, 20000)
        print_it()
        progress(20.0)
        self.assertEqual(construct.left_to_pay, 22220)
        print_it()
        transaction(20000, "")
        self.assertEqual(construct.left_to_pay, 2220)
        print_it()
        progress(50.0)
        self.assertEqual(construct.left_to_pay, 35550)
        print_it()
        transaction(35000, "")
        self.assertEqual(construct.left_to_pay, 550)
        print_it()
        progress(75.0)
        self.assertEqual(construct.left_to_pay, 28325)
        print_it()
        transaction(30000, "")
        self.assertEqual(construct.left_to_pay, -1675)
        print_it()
        progress(100.0)
        self.assertEqual(construct.left_to_pay, 26100)
        print_it()
        transaction(26100, "")
        self.assertEqual(construct.left_to_pay, 0)
        print_it()

    def test_deposit_main_side(self):
        construct = Construct(title_text="Deposit holder",
                              vat_percent_num=15.0,
                              company_profit_percent_num=14.0,
                              owner_profit_coeff=0.13)
        construct.save()
        choice1 = Choice(construct=construct,
                         name_txt="Floor",
                         quantity_num = 25.,
                         price_num=1000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice1.save()
        choice2 = Choice(construct=construct,
                         name_txt="Walls",
                         quantity_num = 4.,
                         price_num=10000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice2.save()
        choice3 = Choice(construct=construct,
                         name_txt="Roof",
                         quantity_num = 35.,
                         price_num=1000,
                         plan_days_num=3.,
                         main_contract_choice=True)
        choice3.save()
        choice4 = Choice(construct=construct,
                         name_txt="Shed",
                         quantity_num = 1.,
                         price_num=30000,
                         plan_days_num=3.,
                         main_contract_choice=False)
        choice4.save()

        def print_it():
            return
            print("         >>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<")
            print(f"Progress: {construct.overall_progress_percent()}%; " +
                  f"Full cost: {construct.full_cost}; " +
                  f"Main cost: {construct.main_cost}; " +
                  f"Paid deposit: {construct.deposit} ({construct.deposit_percent :.2f}%); " +
                  f"Full progress cost: {construct.full_progress_cost};\n" +
                  f"Deposit aware progress cost: {construct.no_deposit_progress_cost} + " +
                  f"{construct.full_side_progress_cost} = " +
                  f"{construct.no_deposit_progress_cost + construct.full_side_progress_cost}; " +
                  f"Income: {construct.round_income}; Outcome: {construct.round_outcome}; " +
                  f"Left to pay: {construct.left_to_pay}")

        def transaction(amo, det):
            # print(f"---------> Transaction: {amo}, {det}")
            ta = Transaction(construct=construct, from_txt="Client", to_txt="Company",
                             amount=amo, details_txt=det,
                             transaction_type="IN")
            ta.save()

        def progress(val):
            # print(f"--------> Progress: {val}%")
            choice1.progress_percent_num = val; choice1.save()
            choice2.progress_percent_num = val; choice2.save()
            choice3.progress_percent_num = val; choice3.save()
            choice4.progress_percent_num = val; choice4.save()

        print_it()
        # transaction(construct.main_cost * 0.15, "#deposit")
        transaction(20000, "#deposit")
        self.assertEqual(construct.deposit, 20000)
        print_it()
        progress(20.0)
        self.assertEqual(construct.left_to_pay, 30086)
        print_it()
        transaction(30000, "")
        self.assertEqual(construct.left_to_pay, 86)
        print_it()
        progress(50.0)
        print_it()
        transaction(45000, "")
        self.assertEqual(construct.left_to_pay, 215)
        print_it()
        progress(75.0)
        self.assertEqual(construct.left_to_pay, 37823)
        print_it()
        transaction(40000, "")
        self.assertEqual(construct.left_to_pay, -2177)
        print_it()
        progress(100.0)
        self.assertEqual(construct.left_to_pay, 35430)
        print_it()
        transaction(26100 + 9330, "")
        self.assertEqual(construct.left_to_pay, 0)
        print_it()

    def test_get_struct_signature(self):
        construct1 = Construct(title_text="Number one")
        construct2 = Construct(title_text="Number two")
        construct3 = Construct(title_text="Number three")
        struct1 = {
                   'line_1': {'type': 'Header2', 'id': 'First header'},
                   'line_2': {'type': 'Choice', 'id': '1'},
                   'line_3': {'type': 'Choice', 'id': '2'},
                   'line_4': {'type': 'Header2', 'id': 'Second header'},
                   'line_5': {'type': 'Choice', 'id': '3'},
                   'line_6': {'type': 'Choice', 'id': '4'},
                   'line_7': {'type': 'Choice', 'id': '5'},
                  }
        construct1.struct_json = json.dumps(struct1)
        struct2 = {
                   'line_1': {'type': 'Header2', 'id': 'First header'},
                   'line_2': {'type': 'Choice', 'id': '6'},
                   'line_3': {'type': 'Choice', 'id': '7'},
                   'line_4': {'type': 'Choice', 'id': '8'},
                   'line_5': {'type': 'Header2', 'id': 'Second header'},
                   'line_6': {'type': 'Choice', 'id': '9'},
                   'line_7': {'type': 'Choice', 'id': '10'},
                   'line_8': {'type': 'Choice', 'id': '11'},
                  }
        construct2.struct_json = json.dumps(struct2)
        struct3 = {
                   'line_1': {'type': 'Header2', 'id': 'header one'},
                   'line_2': {'type': 'Choice', 'id': '12'},
                   'line_3': {'type': 'Choice', 'id': '13'},
                   'line_4': {'type': 'Header2', 'id': 'header two'},
                   'line_5': {'type': 'Choice', 'id': '14'},
                   'line_6': {'type': 'Choice', 'id': '15'},
                   'line_7': {'type': 'Choice', 'id': '16'},
                  }
        construct3.struct_json = json.dumps(struct3)
        construct1.save()
        construct2.save()
        construct3.save()
        self.assertEqual(construct1.get_struct_signature(), construct3.get_struct_signature())
        self.assertFalse(construct1.get_struct_signature() == construct2.get_struct_signature())

    def test_get_slug(self):
        construct1 = make_test_construct("First one", history=True)
        construct2 = make_test_construct("Second construct", history=True)
        construct3 = make_test_construct("Третий конструкт, ё!", history=True)
        construct1.save()
        construct2.save()
        construct3.save()
        s1 = construct1.get_slug()
        s2 = construct2.get_slug()
        s3 = construct3.get_slug()
        self.assertTrue(len(s1.strip()) > 0)
        self.assertTrue(len(s2.strip()) > 0)
        self.assertTrue(len(s3.strip()) > 0)


    def test_dump_all_constructs(self):
        construct1 = make_test_construct("First one", history=True)
        construct2 = make_test_construct("Second construct", history=True)
        construct3 = make_test_construct("The third buddy", history=True)
        dirname = 'test_folder_for_tests'
        if not os.access(dirname, os.F_OK):
            os.mkdir(dirname)
        dump_all_constructs(dirname)
        files = [f for f in os.listdir(dirname)]
        self.assertEqual(len(files), 3)
        for f in files:
            os.remove(dirname + '/' + f)
        os.rmdir(dirname)

    def test_dump_and_load_all_constructs(self):
        construct1 = make_test_construct("First one", history=True)
        construct2 = make_test_construct("Second construct", history=True)
        construct3 = make_test_construct("The third buddy", history=True)
        dirname = 'test_folder_for_tests'
        if not os.access(dirname, os.F_OK):
            os.mkdir(dirname)
        dump_all_constructs(dirname)
        construct1.delete()
        construct2.delete()
        construct3.delete()
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 0)
        load_all_constructs(dirname)
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 3)
        files = [f for f in os.listdir(dirname)]
        for f in files:
            os.remove(dirname + '/' + f)
        os.rmdir(dirname)

    def test_construct_get_stat(self):
        construct = make_test_construct()
        construct.save()
        stat = construct.get_stat()
        fname='test_construct_get_stat.json'
        construct.export_to_json(fname)
        new_construct = Construct.safe_import_from_json(fname)
        new_stat = new_construct.get_stat()
        self.assertEqual(stat, new_stat)
        os.remove(fname)

    def test_add_as_on_page(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        Transaction.add_as_on_page(construct, 'Me', 'Him', 3.33, 'OUT', '2023-07-15', '2307151230', 'some details')
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 1)

    def test_invoice_shallow_copy(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        invoice.transactions.add(ta)
        invoice.save()
        invtras = InvoiceTransaction.objects.all()
        for intra in invtras:
            intra.construct = construct
            intra.save()
        new_invoice = invoice.shallow_copy(construct)
        new_invoice.save()
        invoices = Invoice.objects.all()
        self.assertEqual(len(invoices), 2)
        print('invoices[0].id: ', invoices[0].id)
        print('invoices[1].id: ', invoices[1].id)
        self.assertEqual(len(invoices[0].transactions.all()), 0)
        self.assertEqual(len(invoices[1].transactions.all()), 1)

    def test_transaction_shallow_copy(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        trans = Transaction.add(construct, 100.0, direction='in')
        new_trans = trans.shallow_copy(construct)
        new_trans.save()
        transs = Transaction.objects.all()
        self.assertEqual(len(transs), 2)

    def test_choice_shallow_copy(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        new_choice = choice.shallow_copy(construct)
        new_choice.save()
        choices = Choice.objects.all()
        self.assertEqual(len(choices), 2)

    def test_construct_shallow_copy(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        dic = {"line_1": {"type": "Header2", "id": "Some header"}}
        dic["line_2"] = {"type": "Choice", "id": str(choice.id)}
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        dic["line_3"] = {"type": "Choice", "id": str(choice.id)}
        construct.struct_json = json.dumps(dic)
        construct.save()
        new_construct = construct.shallow_copy()
        new_construct.save()
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 2)


    def test_copy_construct(self):
        construct = Construct(title_text='Original Construct')
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        dic = {"line_1": {"type": "Header2", "id": "Some header"}}
        dic["line_2"] = {"type": "Choice", "id": str(choice.id)}
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        dic["line_3"] = {"type": "Choice", "id": str(choice.id)}
        construct.struct_json = json.dumps(dic)
        construct.save()
        new_construct = construct.copy('Copy of ' + construct.title_text)
        json1_dic = json.loads(construct.struct_json)
        json2_dic = json.loads(new_construct.struct_json)
        self.assertEqual(len(json1_dic.keys()), len(json2_dic.keys()))
        self.assertIs(construct.struct_json == new_construct.struct_json, False)

    def test_construct_export_import_invoice_transaction(self):
        construct_name = 'Some test Construct'
        construct = Construct(title_text=construct_name)
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '-',
             constructive_notes    = 'be yourself',
             client_notes          = 'show me',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        ta.invoice_set.add(invoice)
        ta.save()
        inv_tra = ta.invoicetransaction_set.all()
        for intra in inv_tra:
            intra.construct = construct
            intra.save()
        fname = 'test_export_construct_export_import.json'
        construct.export_to_json(fname)
        construct.delete()
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 0)
        Construct.safe_import_from_json(fname)
        cons = Construct.objects.all()
        self.assertEqual(cons[0].title_text, "Imported: " + construct_name)
        os.remove(fname)
        invtra = InvoiceTransaction.objects.all()
        self.assertEqual(len(invtra), 1)

    def test_construct_safe_import(self):
        construct_name = 'Some test Construct'
        construct = Construct(title_text=construct_name)
        construct.save()
        struct_dic = {}
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        struct_dic['line_1'] = {'type': 'Choice', 'id': str(choice.id)}
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '-',
             constructive_notes    = 'be yourself',
             client_notes          = 'show me',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        struct_dic['line_2'] = {'type': 'Choice', 'id': str(choice.id)}
        construct.struct_json = json.dumps(struct_dic)
        construct.save()
        struct_json1 = construct.struct_json
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        ta.invoice_set.add(invoice)
        ta.save()
        inv_tra = ta.invoicetransaction_set.all()
        for intra in inv_tra:
            intra.construct = construct
            intra.save()
        fname = 'test_export_construct_export_import.json'
        construct.export_to_json(fname)
        construct.delete()
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 0)
        Construct.safe_import_from_json(fname)
        cons = Construct.objects.all()
        self.assertEqual(cons[0].title_text, 'Imported: ' + construct_name)
        struct_json2 = cons[0].struct_json
        self.assertIs(struct_json1 == struct_json2, False)
        os.remove(fname)
        invtra = InvoiceTransaction.objects.all()
        self.assertEqual(len(invtra), 1)

    def test_construct_export_import(self):
        print('>>> test_construct_export_import() <<<')
        construct_name = 'Some test Construct'
        construct = Construct(title_text=construct_name)
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '-',
             constructive_notes    = 'be yourself',
             client_notes          = 'show me',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        fname = 'test_export_construct_export_import.json'
        construct.export_to_json(fname)
        construct.delete()
        cons = Construct.objects.all()
        self.assertEqual(len(cons), 0)
        Construct.safe_import_from_json(fname)
        cons = Construct.objects.all()
        self.assertEqual(cons[0].title_text, "Imported: " + construct_name)
        os.remove(fname)

    def test_construct_export_to_json(self):
        print('>>> test_construct_export_to_json() <<<')
        construct = Construct(title_text='Some Test Construct')
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '-',
             constructive_notes    = 'be yourself',
             client_notes          = 'show me',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        test_file = '.test_file_json'
        construct.export_to_json(test_file)

    def test_overall_progress_percent(self):
        construct = Construct()
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 2',
             notes_txt             = '',
             quantity_num          = 2,
             price_num             = '20.0',
             progress_percent_num  = 25.0,
             units_of_measure_text = 'nr',
             workers               = 'Paul',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 7.0)
        choice.save()
        progress = construct.overall_progress_percent()
        self.assertEqual(progress, 100.*13.5/50)

    def test_progress_cost(self):
        construct = Construct()
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        cost = construct.progress_cost()
        self.assertIs(np.allclose([cost], [3.5]), True)

    def test_same_direction_of_invoice_and_its_transactions_2(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        ta.invoice_set.add(invoice)
        result = ''
        try:
            invoice.save()
            result = 'saved'
        except:
            result = 'impossible'
        self.assertIs(result, 'saved')

    def test_same_direction_of_invoice_and_its_transactions_1(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='out')
        ta.invoice_set.add(invoice)
        result = ''
        try:
            invoice.save()
            result = 'saved'
        except:
            result = 'impossible'
        self.assertIs(result, 'impossible')

    def test_outcoming_invoice_paid(self):
        pass

    def test_incoming_invoice_paid(self):
        pass

    def test_construct_income(self):
        construct = Construct()
        construct.save()
        ta1 = Transaction.add(construct, 100.0)
        ta2 = Transaction.add(construct, 130.0)
        ta3 = Transaction.add(construct, 50.0, direction='out')
        ta4 = Transaction.add(construct, 75.0, direction='out')
        construct.transaction_set.add(ta1, ta2, ta3, ta4)
        income = construct.income()
        self.assertEqual(round(income), 230)
        ta5 = Transaction.add(construct, 15.0, direction='in')
        construct.transaction_set.add(ta5)
        income = construct.income()
        self.assertEqual(round(income), 245)

    def test_construct_debt(self):
        construct = Construct()
        construct.save()
        iv1 = Invoice.add(construct, "John", 100.0)
        iv2 = Invoice.add(construct, "Paul", 130.0)
        iv3 = Invoice.add(construct, "George", 50.0, direction='out')
        iv4 = Invoice.add(construct, "Ringo", 75.0, direction='out')
        construct.invoice_set.add(iv1, iv2, iv3, iv4)
        debt = construct.debt()
        self.assertEqual(round(debt), 105)
        iv5 = Invoice.add(construct, "xxx", 15.0, direction='in')
        construct.invoice_set.add(iv5)
        debt = construct.debt()
        self.assertEqual(round(debt), 120)

    def test_construct_balance(self):
        construct = Construct()
        construct.save()
        ta1 = Transaction.add(construct, 100.0)
        ta2 = Transaction.add(construct, 130.0)
        ta3 = Transaction.add(construct, 50.0, direction='out')
        ta4 = Transaction.add(construct, 75.0, direction='out')
        construct.transaction_set.add(ta1, ta2, ta3, ta4)
        balance = construct.balance()
        self.assertEqual(round(balance), 105)

    def test_add_invoice_to_transaction(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, due='2023-05-13')
        ta = Transaction.add(construct, 100.0)
        ta.invoice_set.add(invoice)
        self.assertIs(invoice.amount - ta.amount < 1.e-10, True)

    def test_add_transaction_to_invoice(self):
        construct = Construct(title_text='Test project add_transaction_to_invoice()')
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, due='2023-05-13')
        ta = Transaction.add(construct, 100.0)
        invoice.transactions.add(ta)
        invoice.save()
        self.assertIs(invoice.amount - ta.amount < 1.e-10, True)

    def test_transaction_1(self):
        construct = Construct()
        construct.save()
        ta = Transaction.add(construct, 10.0)
        self.assertIs(ta.id > 0, True)

    def test_add_invoice_method_7(self):
        construct = Construct()
        construct.save()
        invoice_id = None
        try:
            invoice = Invoice.add(construct, "John Smith", 100.0, due='May 13, 2023')
        except:
            invoice = None
        self.assertIs(invoice, None)

    def test_add_invoice_method_6(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, due='2023-05-13')
        self.assertIs(invoice.id > 0, True)

    def test_add_invoice_method_5(self):
        construct = Construct()
        construct.save()
        invoice_id = None
        try:
            invoice = Invoice.add(construct, "John Smith", 100.0, issued='May 13, 2023')
        except:
            invoice = None
        self.assertIs(invoice, None)

    def test_add_invoice_method_4(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, issued='2023-05-13')
        self.assertIs(invoice.id > 0, True)

    def test_add_invoice_method_3(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='nah')
        self.assertIs(invoice, None)

    def test_add_invoice_method_2(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='out')
        self.assertIs(invoice.id > 0, True)

    def test_add_invoice_method_1(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        self.assertIs(invoice.id > 0, True)

    def test_add_incoming_invoice_method(self):
        construct = Construct()
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0)
        self.assertIs(invoice.id > 0, True)

    def test_add_incoming_invoice(self):
        print("\n>>> test_add_incoming_invoice() <<<")
        construct = Construct()
        construct.save()
        invoice = Invoice()
        invoice.amount = 10.0
        invoice.type = Transaction.TYPES[0]
        invoice.issue_date = dt.datetime.now()
        invoice.due_date = dt.datetime.now()
        invoice.construct = construct
        invoice.seller = "Vasya"
        invoice.save()
        self.assertIs(invoice.id > 0, True)


class PayInvoicesTests(TestCase):
    def test_page_access(self):
        User.objects.create_superuser(username='admin', password='secret', email='admin@domain.com')
        c = Client()
        c.login(username="admin", password="secret")
        response = c.get("/list/invoices/payall/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
    
    def test_page_access_redirect(self):
        User.objects.create_user(username='user', password='secret', email='admin@domain.com')
        c = Client()
        c.login(username="user", password="secret")
        response = c.get("/list/invoices/payall/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
    
    def test_view(self):
        con1 = make_test_construct("Derby")
        con1.vat_percent_num = 5
        con1.save()
        con2 = make_test_construct("Nottingham")
        con2.vat_percent_num = 15
        con2.save()
        con3 = make_test_construct("Loughborough")
        con3.vat_percent_num = 20
        con3.save()
        con4 = make_test_construct("Southampton")
        con4.vat_percent_num = 5
        con4.save()
        vasya = User.objects.create_user(username="vasya", password="secret")
        kolya = User.objects.create_user(username="kolya", password="secret")
        petya = User.objects.create_user(username="petya", password="secret")
        invoices = {}
        invoices[1] = Invoice(construct=con1, number='0000', amount=300,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='#salary')
        invoices[2] = Invoice(construct=con1, number='0001', amount=3000,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='bla-bla\n#materials')
        invoices[3] = Invoice(construct=con2, number='0000', amount=1300,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='#salary')
        invoices[4] = Invoice(construct=con3, number='0000', amount=500,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='#salary')
        invoices[5] = Invoice(construct=con2, number='0001', amount=400,
                       invoice_type=Transaction.OUTGOING,
                       seller='Kolya', owner=kolya, details_txt='hey\n#salary')
        invoices[6] = Invoice(construct=con2, number='0002', amount=4000,
                       invoice_type=Transaction.OUTGOING,
                       seller='Kolya', owner=kolya, details_txt='hey\n#salary')
        invoices[7] = Invoice(construct=con3, number='0001', amount=1000,
                       invoice_type=Transaction.OUTGOING,
                       seller='Kolya', owner=kolya, details_txt='hey\n#materials')
        invoices[8] = Invoice(construct=con4, number='0001', amount=20000,
                       invoice_type=Transaction.OUTGOING,
                       seller='Kolya', owner=kolya, details_txt='hey\n#materials')
        invoices[9] = Invoice(construct=con3, number='0001', amount=700,
                       invoice_type=Transaction.OUTGOING,
                       seller='Petya', owner=petya, details_txt='hey\n#salary')
        invoices[10] = Invoice(construct=con3, number='0002', amount=100,
                       invoice_type=Transaction.OUTGOING,
                       seller='Petya', owner=petya, details_txt='hey\n#salary')
        invoices[11] = Invoice(construct=con4, number='0001', amount=11700,
                       invoice_type=Transaction.OUTGOING,
                       seller='Petya', owner=petya, details_txt='hey\n#materials')
        invoices[12] = Invoice(construct=con3, number='0001', amount=7700.345,
                       invoice_type=Transaction.OUTGOING,
                       seller='Petya', owner=petya, details_txt='hey\n#salary')
        for v in invoices.values():
            v.save()
        User.objects.create_superuser(username='admin', password='secret', email='admin@domain.com')
        c = Client()
        c.login(username="admin", password="secret")
        response = c.get("/list/invoices/payall/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(str(response.content).find('4,680') >= 0)
        self.assertTrue(str(response.content).find('24,520') >= 0)
        self.assertTrue(str(response.content).find('18,500') >= 0)
    
    def test_submit(self):
        con1 = make_test_construct("Derby")
        con1.vat_percent_num = 5
        con1.save()
        User.objects.create_superuser(username='admin', password='secret', email='admin@domain.com')
        c = Client()
        c.login(username="admin", password="secret")
        vasya = User.objects.create_user(username="vasya", password="secret")
        inv1 = Invoice(construct=con1, number='0000', amount=300,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='#salary')
        inv2 = Invoice(construct=con1, number='0001', amount=3000,
                       invoice_type=Transaction.OUTGOING,
                       seller='Vasya', owner=vasya, details_txt='bla-bla\n#materials')
        inv1.save(); inv2.save()
        response = c.get("/list/invoices/payall/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        # import pdb; pdb.set_trace()
        context_inv1 = response.context['subsets'][0]['invoices'][0]
        context_inv2 = response.context['subsets'][0]['invoices'][1]
        post_data = {f'invoice_id_{context_inv1["id"]}': [f'{context_inv1["id"]}'],
                     f'amount_{context_inv1["id"]}': [f'{context_inv1["amount"]}'],
                     f'full_amount_{context_inv1["id"]}': [f'{context_inv1["was_amount"]}'],
                     f'box_{vasya.id}_{context_inv1["id"]}': ['on'],
                     f'invoice_id_{context_inv2["id"]}': [f'{context_inv2["id"]}'],
                     f'amount_{context_inv2["id"]}': [f'{context_inv2["amount"]}'],
                     f'full_amount_{context_inv2["id"]}': [f'{context_inv2["was_amount"]}'],
                     f'box_{vasya.id}_{context_inv2["id"]}': ['on']}
        tra_count1 = len(Transaction.objects.all())
        invtra_count1 = len(InvoiceTransaction.objects.all())
        outcome1 = con1.outcome()
        response = c.post("/list/invoices/payall/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        tra_count2 = len(Transaction.objects.all())
        invtra_count2 = len(InvoiceTransaction.objects.all())
        con1.numbers = {}
        outcome2 = con1.outcome()
        self.assertEqual(tra_count2, tra_count1 + 2)
        self.assertEqual(invtra_count2, invtra_count1 + 2)
        self.assertEqual(outcome2 - outcome1, 3300)


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='yuran', password='secret', email='yuran@domain.com')
        self.simple_user = User.objects.create_user(username='simple', password='secret', email='simple@domain.com')
        self.simple_user.save()
        self.client_user = User.objects.create_user(username='client',
                password='secret',
                email='client@domain.com')
        permission = Permission.objects.get(codename='view_construct')
        self.client_user.user_permissions.add(permission)
        self.worker_user = User.objects.create_user(username='worker',
                password='secret',
                email='worker@domain.com')
        permission = Permission.objects.get(codename='add_invoice')
        self.worker_user.user_permissions.add(permission)

        # worker in the Workers group
        workers_group, _ = Group.objects.get_or_create(name=WORKER_GROUP_NAME)
        content_type = ContentType.objects.get_for_model(Invoice)
        add_invoice_permission, _ = Permission.objects.get_or_create(
            codename='add_invoice',
            name='Can add invoice',
            content_type=content_type,
        )
        view_invoice_permission, _ = Permission.objects.get_or_create(
            codename='view_invoice',
            name='Can view invoice',
            content_type=content_type,
        )
        change_invoice_permission, _ = Permission.objects.get_or_create(
            codename='change_invoice',
            name='Can change invoice',
            content_type=content_type,
        )
        workers_group.permissions.add(add_invoice_permission, view_invoice_permission, change_invoice_permission)
        self.worker_user_2 = User.objects.create_user('worker2', 'worker@example.com', 'secret')
        self.worker_user_2.groups.add(workers_group)

        # client in the Clients group
        clients_group, _ = Group.objects.get_or_create(name=CLIENT_GROUP_NAME)
        content_type = ContentType.objects.get_for_model(Invoice)
        self.client_user_2 = User.objects.create_user('client2', 'client@example.com', 'secret')
        self.client_user_2.groups.add(clients_group)

    def test_session_extension_on_detail_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        session = c.session
        session['key'] = 'value'
        one_hour = 60 * 60
        session.set_expiry(one_hour)
        session.save()
        response = c.get("/list/" + str(cons.id) + '/')
        session = c.session
        updated_date = session.get_expiry_date()
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertAlmostEqual(updated_date - timezone.now(), timedelta(days=1), delta=timedelta(seconds=5))

    def test_actions_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/actions/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_db_backup(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/backup/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find('File copied') > 0, True)


    def test_db_backup_twice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/backup/")
        response = c.get("/list/backup/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find('File already exists') > 0, True)


    def test_transactions_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/" + str(cons.id) + "/transactions/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/transactions/?direction=all")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/transactions/?direction=in")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/transactions/?direction=out")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/transactions/?direction=salary")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/transactions/?direction=expenses")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_transactions_page_redirect(self):
        c = Client()
        c.login(username="client", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/" + str(cons.id) + "/transactions/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_invoice_ownership(self):
        c = Client()
        c.login(username="worker", password="secret")
        construct = Construct(title_text='Original Construct')
        construct.save()
        invoice = Invoice.add(construct, "John Smith", 100.0, direction='in')
        ta = Transaction.add(construct, 100.0, direction='in')
        invoice.transactions.add(ta)
        invoice.owner = self.worker_user
        invoice.save()
        worker_invoices = self.worker_user.invoice_set.all()
        self.assertEqual(len(worker_invoices), 1)

    def test_invoices_page_redirect(self):
        c = Client()
        c.login(username="client", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/" + str(cons.id) + "/invoices/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_invoices_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/list/" + str(cons.id) + "/invoices/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get("/list/" + str(cons.id) + "/invoices/?direction=in")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_session_extension_on_client_page(self):
        cons = make_test_construct('Test construct for the client session')
        self.client_user_2.accessible_constructs.add(cons)
        c = Client()
        c.login(username="client2", password="secret")
        session = c.session
        session['key'] = 'value'
        one_hour = 60 * 60
        session.set_expiry(one_hour)
        session.save()
        response = c.get("/list/" + str(cons.id) + '/client/')
        session = c.session
        updated_date = session.get_expiry_date()
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertAlmostEqual(updated_date - timezone.now(), timedelta(days=1), delta=timedelta(seconds=5))

    def test_login_page_list(self):
        c = Client()
        response = c.get('/list/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_account_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_account_page_worker(self):
        c = Client()
        c.login(username="worker2", password="secret")
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_account_page_client(self):
        c = Client()
        c.login(username="client2", password="secret")
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_account_page_foreman(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = make_test_construct('Test construct for the foreman session')
        cons.foreman = self.worker_user_2
        cons.save()
        cat = Category(name='active', priority=1)
        cat.save(0)
        cat.constructs.add(cons.id)
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(str(response.content).find("Test construct for the foreman session") >= 0)

    def test_account_page_foreman_2(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = make_test_construct('Test construct for the foreman session')
        cons.foreman = self.worker_user_2
        cons.save()
        cat = Category(name='Windows (Active)', priority=1)
        cat.save(0)
        cat.constructs.add(cons.id)
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(str(response.content).find("Test construct for the foreman session") >= 0)

    def test_account_page_foreman_3(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = make_test_construct('Test construct for the foreman session')
        cons.foreman = self.worker_user_2
        cons.save()
        cat = Category(name='Windows (Done)', priority=1)
        cat.save(0)
        cat.constructs.add(cons.id)
        response = c.get('/list/account/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(str(response.content).find("Test construct for the foreman session") >= 0)

    def test_worker_page_foreman(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = make_test_construct('Test construct for the client session')
        cons.foreman = self.worker_user_2
        cons.save()
        response = c.get('/list/' + str(cons.id) + '/worker/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("price") > 0, True)

    def test_worker_page(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = make_test_construct('Test construct for the client session')
        response = c.get('/list/' + str(cons.id) + '/worker/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("price") > 0, False)

    def test_empty_list(self):
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_non_empty_list(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        choices = Choice.objects.all()
        self.assertEqual(len(choices), 9)
        choices[0].main_contract_choice = True
        choices[0].progress_percent_num = 30
        choices[0].save()
        ta = Transaction.add(con1, 100.0, direction='in')
        ta.details_txt = '#deposit'
        ta.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_categories(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat1.constructs.add(con1.id)
        cat1.constructs.add(con2.id)
        cat2.constructs.add(con3.id)
        cat1.save()
        cat2.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get('/list/?category=' + str(cat1.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_combined_categories(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat1.constructs.add(con1.id)
        cat1.constructs.add(con2.id)
        cat2.constructs.add(con3.id)
        cat1.save()
        cat2.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get('/list/?category=' + str(cat1.id) + ',' + str(cat2.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_combined_categories_and_foreman(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat1.constructs.add(con1.id)
        cat1.constructs.add(con2.id)
        cat2.constructs.add(con3.id)
        cat1.save()
        cat2.save()
        foreman = User(username='foreman')
        foreman.save()
        con1.foreman = foreman
        con3.foreman = foreman
        con1.save()
        con3.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        get_str = '/list/?category=' + str(cat1.id) + ',' + str(cat2.id) + '&foreman=' + str(foreman.id)
        response = c.get(get_str)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("Number one") > 0, True)
        self.assertIs(str(response.content).find("Number two") > 0, False)
        self.assertIs(str(response.content).find("Number three") > 0, True)

    def test_empty_categories(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat1.constructs.add(con1.id)
        cat1.constructs.add(con2.id)
        cat2.constructs.add(con3.id)
        cat1.save()
        cat2.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        response = c.get('/list/?category=')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_update_construct_category(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        cat1 = Category(name='one', priority=0)
        cat2 = Category(name='two', priority=1)
        cat1.save()
        cat2.save()
        cat2.constructs.add(con2.id)
        cat2.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(len(cat1.constructs.all()), 2)

    def test_update_construct_category_with_no_categories(self):
        c = Client()
        c.login(username="yuran", password="secret")
        con1 = make_test_construct(construct_name="Number one")
        con2 = make_test_construct(construct_name="Number two")
        con3 = make_test_construct(construct_name="Number three")
        con1.save()
        con2.save()
        con3.save()
        response = c.get('/list/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_login_page_detail(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_detail_page_markup(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct()
        cons.save()
        choice = make_test_choice(cons, name='Choice with a **bolddd** name')
        choice.save()
        response = c.get('/list/' + str(cons.id) +'/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("<b>bolddd</b>") > 0, True)

    def test_detail_page_markup_amp(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct()
        cons.save()
        choice = make_test_choice(cons, name='Choice with a R&amp;D name')
        choice.save()
        response = c.get('/list/' + str(cons.id) +'/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("R&amp;D") > 0, True)

    def test_login_page_client_view(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/client/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_login_page_flows(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/flows/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_login_page_transactions(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_transactions_page_accessed(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_transactions_page_no_access(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_login_page_gantt(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/gantt/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_call_flows_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_call_flows_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_call_gantt_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/gantt/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_call_client_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/client/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_view_invoice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        invs = Invoice.objects.all()
        inv = invs[0]
        inv.details_txt = 'Description on this invoice'
        inv.save()
        response = c.get("/list/invoice/" + str(inv.id) + "/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_view_transaction(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        tas = Transaction.objects.all()
        ta = tas[0]
        ta.details_txt = 'Description on this transaction'
        ta.save()
        response = c.get("/list/transaction/" + str(ta.id) + "/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_transaction_bunch_page_access(self):
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/bunch/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_transaction_bunch_page_no_access(self):
        c = Client()
        c.login(username="worker2", password="secret")
        response = c.get("/list/transaction/bunch/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_transaction_bunch(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        post_data = {'construct_id': ['1'], 'delimiter': ['2'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey, Yury, 5000, IN, 26/08/2023, 012341200, money for good life\r\n' + \
                               'Marcos, Yury, 7000, IN, 30/08/2023, 77777, profit sharing']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 3)

    def test_transaction_bunch_sum(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = Construct(title_text='Test construct')
        construct.save()
        post_data = {'construct_id': ['1'], 'delimiter': ['2'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey, Yury, 5000, IN, 26/08/2023, 012341200, money for good life\r\n' + \
                               'Marcos, Yury, 7000, IN, 30/08/2023, 77777, profit sharing']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 2)
        total = sum([t.amount for t in tras])
        self.assertEqual(total, 12000)

    def test_transaction_bunch_with_negative(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = Construct(title_text='Test construct')
        construct.save()
        post_data = {'construct_id': ['1'], 'delimiter': ['2'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey, Yury, 5000, IN, 26/08/2023, 012341200, money for good life\r\n' + \
                               'Marcos, Yury, 7000, IN, 30/08/2023, 77777, profit sharing\r\n' + \
                               'Home Office, Yury, -3000, OUT, 12/12/2023, eeee, IHS Refund']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 3)
        total = sum([t.amount for t in tras])
        self.assertEqual(total, 9000)

    def test_transaction_bunch_tab(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        post_data = {'construct_id': ['1'], 'delimiter': ['1'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey\t Yury\t 5000\t IN\t 26/08/2023\t 012341200\t money for good life\r\n' + \
                               'Marcos\t Yury\t 7000\t IN\t 30/08/2023\t 77777\t profit sharing']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 3)

    def test_transaction_bunch_bad_construct(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        post_data = {'construct_id': ['15'], 'delimiter': ['2'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey, Yury, 5000, IN, 26/08/2023, 012341200, money for good life\r\n' + \
                               'Marcos, Yury, 7000, IN, 30/08/2023, 77777, profit sharing']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(len(response.context['errors']) > 0)
        self.assertEqual(response.context['errors'][0].find('getting the construct') >= 0, True)
        tras = construct.transaction_set.all()
        self.assertEqual(len(tras), 1)

    def test_transaction_bunch_bad_type(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        post_data = {'construct_id': [str(construct.id)], 'delimiter': ['2'], 'field_nums': ['1,2,3,4,5,6,7'],
                     'lines': ['Sergey, Yury, 5000,   , 26/08/2023, 012341200, money for good life\r\n' + \
                               'Marcos, Yury, 7000, INO, 30/08/2023, 77777, profit sharing']}
        response = c.post("/list/transaction/bunch/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(len(response.context['errors']), 2)

    def test_call_client_page_client(self):
        cons = Construct()
        cons.save()
        self.client_user_2.accessible_constructs.add(cons)
        c = Client()
        c.login(username="client2", password="secret")
        response = c.get("/list/" + str(cons.id) + "/client/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertIs(str(response.content).find("price") > 0, True)

    def test_call_client_page_non_accessible(self):
        cons = Construct()
        cons.save()
        c = Client()
        c.login(username="client2", password="secret")
        response = c.get("/list/" + str(cons.id) + "/client/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_flows_page_with_invoices(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        Invoice.add(cons, "John", 100.0, direction='in', status='paid')
        Invoice.add(cons, "Paul", 120.0, direction='in', status='unpaid')
        Invoice.add(cons, "George", 102.0, direction='out', status='paid')
        Invoice.add(cons, "Ringo", 123.0, direction='out', status='unpaid')
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_flows_page_with_transactions(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        Transaction.add(cons, 100.0, direction='in',  details='-')
        Transaction.add(cons, 120.0, direction='in',  details='salary')
        Transaction.add(cons, 102.0, direction='out', details='-')
        Transaction.add(cons, 123.0, direction='out', details='SalAry')
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_flows_page_with_invoices_and_transactions(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        Invoice.add(cons, "John", 100.0, direction='in', status='paid')
        Invoice.add(cons, "Paul", 120.0, direction='in', status='unpaid')
        Invoice.add(cons, "George", 102.0, direction='out', status='paid')
        Invoice.add(cons, "Ringo", 123.0, direction='out', status='unpaid')
        Transaction.add(cons, 100.0, direction='in',  details='-')
        Transaction.add(cons, 120.0, direction='in',  details='salary')
        Transaction.add(cons, 102.0, direction='out', details='-')
        Transaction.add(cons, 123.0, direction='out', details='SalAry')
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_open_transaction_submit_form(self):
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_open_transaction_submit_form_populated(self):
        construct = Construct()
        construct.save()
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/?construct=1&to=Ivan Ivanov&amount=100&invoice=29&type=IN&from=Petr Petrov")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(response.context['form']['to_txt'].initial, 'Ivan Ivanov')
        self.assertEqual(response.context['form']['from_txt'].initial, 'Petr Petrov')

    def test_open_transaction_submit_form_populated_2(self):
        construct = Construct()
        construct.save()
        self.user.first_name = "Petr"
        self.user.last_name = "Petrov"
        self.user.save()
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/?construct=1&to=Ivan Ivanov&amount=100&invoice=29&type=IN")
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(response.context['form']['to_txt'].initial, 'Ivan Ivanov')
        self.assertEqual(response.context['form']['from_txt'].initial, 'Petr Petrov')

    def test_open_transaction_submit_form_populated_3(self):
        construct = Construct()
        construct.save()
        self.user.company = "Company Ltd"
        self.user.save()
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/?construct=1&to=Ivan Ivanov&amount=100&invoice=29&type=IN")
        self.user.company = ""
        self.user.save()
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(response.context['form']['to_txt'].initial, 'Ivan Ivanov')
        self.assertEqual(response.context['form']['from_txt'].initial, 'Company Ltd')

    def test_transaction_pay_mismatch(self):
            construct = make_test_construct()
            construct.save()
            invoice = Invoice.add(construct, "John Smith", 100.0, direction='out')
            transac = Transaction.add(construct, 90, direction='out')
            invoice.transactions.add(transac.id)
            invoice.status = Invoice.PAID
            invoice.save()
            c = Client()
            c.login(username="yuran", password="secret")
            request = f"/list/invoice/{str(invoice.id)}/"
            response = c.get(request)
            self.assertEqual(response.status_code, STATUS_CODE_OK)
            self.assertTrue(str(response.content).find('Paid By') >= 0)
            self.assertTrue(str(response.content).find('pay more') >= 0)
            self.assertTrue(invoice.payment_mismatch)

    def test_transaction_pay_match(self):
            construct = make_test_construct()
            construct.save()
            invoice = Invoice.add(construct, "John Smith", 100.0, direction='out')
            transac1 = Transaction.add(construct, 90, direction='out')
            transac2 = Transaction.add(construct, 10, direction='out')
            invoice.transactions.add(transac1.id)
            invoice.transactions.add(transac2.id)
            invoice.status = Invoice.PAID
            invoice.save()
            c = Client()
            c.login(username="yuran", password="secret")
            request = f"/list/invoice/{str(invoice.id)}/"
            response = c.get(request)
            self.assertEqual(response.status_code, STATUS_CODE_OK)
            self.assertTrue(str(response.content).find('Paid By') >= 0)
            self.assertTrue(str(response.content).find('pay more') < 0)

    def test_transaction_multpay_mismatch(self):
            construct = make_test_construct()
            construct.save()
            invoice = Invoice.add(construct, "John Smith", 100.0, direction='out')
            transac1 = Transaction.add(construct, 80, direction='out')
            transac2 = Transaction.add(construct, 10, direction='out')
            invoice.transactions.add(transac1.id)
            invoice.transactions.add(transac2.id)
            invoice.status = Invoice.PAID
            invoice.save()
            c = Client()
            c.login(username="yuran", password="secret")
            request = f"/list/invoice/{str(invoice.id)}/"
            response = c.get(request)
            self.assertEqual(response.status_code, STATUS_CODE_OK)
            self.assertTrue(str(response.content).find('Paid By') >= 0)
            self.assertTrue(str(response.content).find('pay more') >= 0)

    def test_login_transaction_submit_form(self):
        c = Client()
        response = c.get("/list/transaction/submit/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_submit_transaction_form(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_submit_transaction_with_photo(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        dummy_file = get_dummy_image()
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'details_txt': ['note'], 'photo': [dummy_file], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        response = c.get(response.url + "/")
        self.assertEqual(response.context['transaction'].photo.size, dummy_file.size)
        
    def test_login_submit_transaction_form(self):
        c = Client()
        cons = Construct()
        cons.save()
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        
    def test_submit_transaction_form_with_invoice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        invoice = Invoice.add(cons, "John Smith", 100.0, direction='in')
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'invoices': [str(invoice.id)],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_submit_transaction_form_with_invoice_and_get_InvoiceTransaction_object(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        invoice = Invoice.add(cons, "John Smith", 100.0, direction='in')
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'invoices': [str(invoice.id)],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        inv_tra = invoice.invoicetransaction_set.all()
        self.assertEqual(len(inv_tra), 1)

    def test_submit_transaction_form_with_wrong_invoice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        invoice = Invoice.add(cons, "John Smith", 100.0, direction='out')
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'invoices': [str(invoice.id)],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_submit_transaction_form_with_two_invoices(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        invoice1 = Invoice.add(cons, "John", 100.0, direction='in')
        invoice2 = Invoice.add(cons, "Paul", 200.0, direction='in')
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'invoices': [str(invoice1.id), str(invoice2.id)],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_submit_transaction_form_with_two_invoices_and_get_two_InvoiceTransaction_objects(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        invoice1 = Invoice.add(cons, "John", 100.0, direction='in')
        invoice2 = Invoice.add(cons, "Paul", 200.0, direction='in')
        post_data = {'from_txt': ['Vasya'], 'to_txt': ['Petya'], 'amount': ['100'],
                'transaction_type': ['IN'], 'construct': [str(cons.id)], 'date': ['2023-05-20'],
                'initial-date': ['2023-05-20 07:35:12+00:00'], 'receipt_number': ['12345678'],
                'invoices': [str(invoice1.id), str(invoice2.id)],
                'details_txt': ['note'], 'photo': [''], 'initial-photo': ['Raw content']}
        response = c.post("/list/transaction/submit/", post_data)
        inv_tra = cons.invoicetransaction_set.all()
        self.assertEqual(len(inv_tra), 2)

    def test_submit_invoice_form(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_submit_invoice_with_photo(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        dummy_file = get_dummy_image()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': [dummy_file]}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        response = c.get(response.url + "/")
        self.assertEqual(response.context['invoice'].photo.size, dummy_file.size)

    def test_modify_invoice_get(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'owner': [str(self.user.id)], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        response = c.get(f"/list/invoice/{invoice.id}/modify/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(type(response.context['form'].fields['owner'].widget), Select)

    def test_modify_invoice_get_worker2(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'owner': [str(self.worker_user_2.id)], 'amount': ['100'],
                'invoice_type': ['OUT'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        response = c.get(f"/list/invoice/{invoice.id}/modify/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(type(response.context['form'].fields['owner'].widget), HiddenInput)

    def test_get_printed_invoice_lines(self):
        details = '1, a, b, c'
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1, a, b, '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1, a, b '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1, a,  '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1, a  '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1,   '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        details = '1   '
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]), 5)
        
    def test_get_printed_invoice_lines_2(self):
        details = '1, a, b, c\n 2, b, c'
        out = get_printed_invoice_lines(details)
        self.assertEqual(len(out), 2)
        self.assertEqual(len(out[0]), 5)
        self.assertEqual(len(out[1]), 5)

    def test_process_invoice_lines(self):
        details = '1 hour, roof, 40\n' +  \
                  '3 hour, floor, 50\n' + \
                  '7 m2, wall, 1500'
        lines = get_printed_invoice_lines(details)
        lines, amount = process_invoice_lines(lines)
        self.assertEqual(lines[0]['amount'], 40.)
        self.assertEqual(lines[1]['amount'], 150.)
        self.assertEqual(lines[2]['amount'], 10500.)
        self.assertEqual(amount, 10690.)

    def test_get_number(self):
        line = '1'
        out = get_number(line)
        self.assertEqual(out, 1.0)
        line = '12'
        out = get_number(line)
        self.assertEqual(out, 12.0)
        line = 12
        out = get_number(line)
        self.assertEqual(out, 12.0)
        line = '12,000'
        out = get_number(line)
        self.assertEqual(out, 12000.0)
        line = 'a12,000'
        # import pdb; pdb.set_trace()
        out = get_number(line)
        self.assertEqual(out, 12000.0)
        line = '  12,000'
        out = get_number(line)
        self.assertEqual(out, 12000.0)
        line = ' ab , 12,000'
        out = get_number(line)
        self.assertEqual(out, 12000.0)
        line = ' ab , 12,000 kc..., 00'
        out = get_number(line)
        self.assertEqual(out, 12000.0)
        line = ' ab , 0'
        out = get_number(line)
        self.assertEqual(out, 0.0)
        line = ' ab , klsje  dl'
        out = get_number(line)
        self.assertEqual(out, 0.0)

    def test_print_invoice_warning(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['1, desr, 20, 20 \n 2, descr2, 30, 60'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        response = c.get(f"/list/invoice/{invoice.id}/print/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(len(response.context['warning']) > 0)

    def test_print_invoice_no_warning(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['1 nr, desr, 20\n 2 hour, descr2, 40'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        response = c.get(f"/list/invoice/{invoice.id}/print/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertTrue(len(response.context['warning']) == 0)

    def test_submit_invoice_simple(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['1 nr, desr, 20\n 2 hour, descr2, 40'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        self.assertIs(response.url.find('accounts/login') >= 0, True)

    def test_print_invoice_no_warning_simple(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['1 nr, desr, 20\n 2 hour, descr2, 40'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        c = Client()
        # a simple user should not be able to get the print page
        c.login(username="simple", password="secret")
        response = c.get(f"/list/invoice/{invoice.id}/print/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        self.assertIs(response.url.find('accounts/login') >= 0, True)

    def test_print_invoice_no_warning_client(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['1 nr, desr, 20\n 2 hour, descr2, 40'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        c = Client()
        # client should not be able to get the print page
        c.login(username="client", password="secret")
        response = c.get(f"/list/invoice/{invoice.id}/print/")
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        self.assertIs(response.url.find('accounts/login') >= 0, True)

    def test_modify_invoice_post(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertIs(response.url.find('accounts/login') >= 0, False)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        post_data['details_txt'] = ['--newdetails']
        new_response = c.post(f"/list/invoice/{invoice.id}/modify/", post_data)
        self.assertEqual(new_response.status_code, STATUS_CODE_REDIRECT)
        invoice = Invoice.objects.latest()
        self.assertIs(str(invoice.details_txt).find("newdetails") >= 0, True)
        
    def test_login_submit_invoice_form(self):
        c = Client()
        cons = Construct()
        cons.save()
        post_data = {'seller': ['Vasya'], 'amount': ['100'],
                'invoice_type': ['IN'], 'construct': [str(cons.id)], 'issue_date': ['2023-05-20'],
                'due_date': ['2023-05-21'], 'number': ['12345678'], 'initial-number': ['12345678'],
                'status': ['Unpaid'], 'initial-issue_date': ['2023-07-12 07:47:28+00:00'],
                'initial-due_date': ['2023-07-12 07:47:28+00:00'], 'initial-photo': ['Raw content'],
                'details_txt': ['note'], 'photo': ['']}
        response = c.post("/list/invoice/submit/", post_data)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
        
    def test_worker_login_to_submit_invoice(self):
        c = Client()
        c.login(username="worker", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/invoice/submit/?construct_id=" +
                str(cons.id) + "&worker")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(type(response.context['form'].fields['owner'].widget), HiddenInput)

    def test_worker2_login_to_submit_invoice(self):
        c = Client()
        c.login(username="worker2", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/invoice/submit/?construct_id=" +
                str(cons.id) + "&worker")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(type(response.context['form'].fields['owner'].widget), HiddenInput)
        self.assertTrue(str(response.content).find('Owner') < 0)

    def test_superuser_login_to_submit_invoice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/invoice/submit/?construct_id=" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(type(response.context['form'].fields['owner'].widget), Select)
        self.assertTrue(str(response.content).find('Owner') >= 0)

    def test_get_fields_submit_invoice(self):
        c = Client()
        c.login(username="worker", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/invoice/submit/?construct_id=" +
                str(cons.id) + "&type=IN" +
                "&details=1,deposit,20000&amount=20000&type=IN")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        self.assertEqual(response.context['form']['amount'].initial, '20000')
        self.assertEqual(response.context['form']['details_txt'].initial, '1,deposit,20000')
        self.assertEqual(response.context['form']['invoice_type'].initial, 'IN')
        
    def test_checkTimeStamp(self):
        print("\n>>> test_checkTimeStamp() <<<")
        construct1 = Construct()
        construct1.save()
        construct2 = Construct()
        construct2.save()
        stamp2 = int(construct2.last_save_date.timestamp()) + 2
        data = {"timestamp" : str(stamp2)}
        result = checkTimeStamp(data, construct1)
        self.assertIs(result, True)


    def test_create_construct(self):
        print("test_create_construct()")
        construct = Construct()
        construct.save()
        print(f"Construct ID: {construct.id}")
        self.assertIs(construct.id is not None, True)


    def test_update_choice_no_update(self):
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == choice_id, True)


    def test_update_choice(self):
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        cells['units'] = 'sq. m.'
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == choice_id, True)


    def test_update_choice_of_huge_id(self):
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        while choice_id < 1200:
            choice_id = create_choice(cell_data, construct)
        cells['units'] = 'sq. m.'
        choice_id = '1,200'
        print("big choice id:", choice_id)
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == 1200, True)


    def test_update_choice_big_quantity(self):
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        cells['quantity'] = '2,100'
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == choice_id, True)


    def test_update_choice_non_existing_choice(self):
        print("test_update_choice_non_existing_choice()")
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        choice_id = '35'
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == -2, True)


    def test_update_choice_delete(self):
        print("test_update_choice_delete()")
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        cells['class'] = 'delete'
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == -1, True)


    def test_update_choice_for_header(self):
        print("test_update_choice_for_header()")
        cells = {'class': '',
                 'name': 'task_name_to_update',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15',
                 'days': '365'}      
        cell_data = {'class': 'Header2', 'cells': cells}
        choice_id = "some header"
        print(f"choice_id: {choice_id}")
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == -1, True)


    def test_create_choice_1(self):
        print("test_create_choice_1()")
        cells = {'class': '',
                 'name': 'task_name',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': '2023-04-15', # focus here 
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        ret = create_choice(cell_data, construct)
        self.assertIs(ret >= 0, True)


    def test_create_choice_2(self):
        print("test_create_choice_2()")
        cells = {'class': '',
                 'name': 'task_name',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': 'April 15, 2023', # focus here
                 'days': '365'}      
        cell_data = {'class': 'Choice delete', 'cells': cells}
        construct = Construct()
        construct.save()
        ret = create_choice(cell_data, construct)
        self.assertIs(ret >= 0, True)


    def test_create_choice_3(self):
        print("test_create_choice_3()")
        cells = {'class': 'delete hello', # focus here
                 'name': 'task_name',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '£100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': 'April 15, 2023',
                 'days': '365'}      
        cell_data = {'class': 'Choice', 'cells': cells}
        construct = Construct()
        construct.save()
        ret = create_choice(cell_data, construct)
        self.assertIs(ret == -1, True)


    def test_create_choice_header(self):
        print("test_create_choice_header()")
        cells = {'class': '',
                 'name': 'task_name',
                 'notes_txt': 'no notes, actually',
                 'quantity': '10.5',
                 'units': 'nr',
                 'price': '100',
                 'assigned_to': 'Universe',
                 'progress': '10%',
                 'day_start': 'April 15, 2023',
                 'days': '365'}      
        cell_data = {'class': 'Header2', 'cells': cells}
        construct = Construct()
        construct.save()
        ret = create_choice(cell_data, construct)
        self.assertIs(ret == -1, True)


    def test_is_dd_mm_yyyy_1(self):
        date = "7/7/2023"
        ret = is_dd_mm_yyyy(date)
        self.assertIs(ret, True)


    def test_is_dd_mm_yyyy_2(self):
        date = "07/7/2023"
        ret = is_dd_mm_yyyy(date)
        self.assertIs(ret, True)


    def test_is_dd_mm_yyyy_3(self):
        date = "7/07/2023"
        ret = is_dd_mm_yyyy(date)
        self.assertIs(ret, True)


    def test_is_dd_mm_yyyy_4(self):
        date = "17/7/2023"
        ret = is_dd_mm_yyyy(date)
        self.assertIs(ret, True)


    def test_is_dd_mm_yyyy_5(self):
        date = "7/17/2023"
        ret = is_dd_mm_yyyy(date)
        self.assertIs(ret, False)


    def test_format_date_1(self):
        date = "August 26, 2023"
        format_date(date)


    def test_format_date_2(self):
        date = "2023-08-26"
        format_date(date)


    def test_format_date_3(self):
        date = "26/08/2023"
        format_date(date)


    def test_format_date_4(self):
        date = "261/108/22023"
        try:
            format_date(date)
            raise Exception("This should fail!")
        except:
            pass


    def test_is_yyyy_mm_dd_1(self):
        date = "2021-01-20"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, True)


    def test_is_yyyy_mm_dd_2(self):
        date = "21-01-20"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, False)


    def test_is_yyyy_mm_dd_3(self):
        date = "January 10, 2021"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, False)


    def test_is_month_day_year_1(self):
        date = "January 10, 2021"
        ret = is_month_day_year(date)
        self.assertIs(ret, True)

    
    def test_is_month_day_year_2(self):
        date = "Jan 10, 2021"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)

    
    def test_is_month_day_year_3(self):
        date = "January 10, 21"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)

    
    def test_is_month_day_year_4(self):
        date = "January     10, 21"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)


    def test_format_date(self):
        construct = make_test_construct()
        for m in range(1, 13):
            for d in [0, 1, 2, 3, 9, 10, 11, 12, 19, 20, 21, 28, 29, 30, 31]:
                for y in [1837, 1900, 1984, 1990, 1991, 2000, 2001, 2018, 2020, 2023, 2025]:
                    date_str = f"{y}-{m}-{d}"
                    choice = make_test_choice(construct)
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except:
                        continue
                    choice.plan_start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    choice.save()
                    date_back = choice.plan_start_date_formatted
                    format_date(date_back)

    
    def test_check_integrity_almost_empty_structure(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in np.random.rand(10) * 100]
        struc_dic = check_integrity('{}', choices)
        print('check_integrity_almost_empty_structure\n', struc_dic)
        self.assertIs(len(struc_dic) == 10, True)


    def test_check_integrity_empty_choices(self):
        choices = []
        struc_dic = check_integrity('  ', choices)
        print('check_integrity_empty_choices\n', struc_dic)
        self.assertIs(len(struc_dic) == 0, True)


    def test_check_integrity_empty_structure(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in np.random.rand(10) * 100]
        struc_dic = check_integrity('  ', choices)
        print('check_integrity_empty_structure\n', struc_dic)
        self.assertIs(len(struc_dic) == 10, True)


    def test_check_integrity_wrong_structure(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
                self.name_txt = str(ID) + "_name"
        np.random.seed(0)
        ids = list(set((np.random.rand(10) * 100).astype(int)))
        choices = [LocalChoice(new_id) for new_id in ids]
        struc_dic = check_integrity('{"line_1":{"type":"Header2", "id":"House"}, "line_2":{"type":"Choice", "id":"37"}}', choices)
        # 37 is not in choices, so it will be gone
        self.assertEqual(len(struc_dic), len(ids)+1)


    def test_check_integrity_right_structure(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
        print('test_check_integrity_right_structure')
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in [10, 15, 23, 44]]
        struc_dic = check_integrity(
            '''{
            "line_1":{"type":"Header2", "id":"House"},
            "line_2":{"type":"Choice", "id":"10"},
            "line_3":{"type":"Choice", "id":"15"},
            "line_4":{"type":"Header2", "id":"Shed"},
            "line_5":{"type":"Choice", "id":"23"},
            "line_6":{"type":"Choice", "id":"44"}
            }''', choices)
        print('check_integrity_right_sturcture\n', struc_dic)
        self.assertIs(len(struc_dic) == 6, True)


    def test_process_post(self):
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 3)


    def test_process_post_markup(self):
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror **bold**", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 3)


    def test_process_post_delete_choice_frontend(self):
        ''' Check if we can delete a choice from the detail.html'''
        # TODO
        pass


    def test_process_post_delete_choice_backend(self):
        ''' Check if we can delete a choice behind the scene
        and not ruin the construct structure.'''
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        choices[0].delete()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 2)


    def test_process_post_add_choice_backend(self):
        ''' Check if we can add a choice behind the scene
        and not ruin the construct structure.'''
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        print(struc_dict)
        self.assertIs(len(struc_dict), 4)


    def test_post_detail_main_choice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon main", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "something smart #main", "client_notes": "bla bla bla"}
    }
  }
}
'''}
        request = Request()
        response = c.post("/list/" + str(construct.id) + "/", request.POST)
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        choices = construct.choice_set.filter(main_contract_choice=True)
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0].name_txt, "Bathtub silicon main")


    def test_process_post_main_choice(self):
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon main", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "something smart #main", "client_notes": "bla bla bla"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        choices = construct.choice_set.filter(main_contract_choice=True)
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0].name_txt, "Bathtub silicon main")


    def test_process_post_with_notes(self):
        print("\n>>> test_process_post_with_notes() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "something smart", "client_notes": "bla bla bla"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 3)


    def test_process_post_client_create_choice(self):
        print("\n>>> test_process_post_client_create_choice() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "my con notes", "client_notes": "his pros notes"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct, client=True)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        # Client can't create neither choice nor header.
        self.assertIs(len(struc_dict), 0)


    def test_process_post_client_update_choice_only(self):
        print("\n>>> test_process_post_client_update_choice_only() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "my con notes", "client_notes": "tricky_str"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 2)
        json_val = json.loads(request.POST['json_value'])
        json_val['row_2']['id'] = 'tr_1'
        request.POST["json_value"] = json.dumps(json_val)
        request.POST["json_value"] = request.POST["json_value"].replace("tricky_str", "updated_str")
        process_post(request, construct, client=True)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 2)
        self.assertEqual(choices[0].client_notes, 'updated_str')


    def test_process_post_client_update_choice(self):
        print("\n>>> test_process_post_client_update_choice() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        choice = Choice(construct=construct,
             name_txt              = 'Choice 1',
             notes_txt             = '-',
             constructive_notes    = 'just do it',
             client_notes          = 'yes, lets go',
             quantity_num          = 1,
             price_num             = '10.0',
             progress_percent_num  = 35.0,
             units_of_measure_text = 'nr',
             workers               = 'John',
             plan_start_date       = '1984-04-15',
             plan_days_num         = 5.0)
        choice.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "tr_1",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "my con notes", "client_notes": "my update"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct, client=True)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 1)
        choice = choices[0]
        self.assertEqual(choice.constructive_notes, 'just do it')
        self.assertEqual(choice.client_notes, 'my update')


    def test_process_post_client_change_order(self):
        print("\n>>> test_process_post_client_change_order() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "something smart", "client_notes": "bla bla bla"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 3)
        json_val = json.loads(request.POST['json_value'])
        json_val['row_2']['id'] = 'tr_1'
        json_val['row_3']['id'] = 'tr_2'
        row_3 = json_val['row_3']
        json_val['row_3'] = dict(json_val['row_2'])
        json_val['row_2'] = dict(row_3)
        request.POST["json_value"] = json.dumps(json_val)
        struct_before = json.dumps(construct.struct_json)
        choice1_name_before = choices[0].name_txt
        process_post(request, construct, client=True)
        struct_after = json.dumps(construct.struct_json)
        self.assertEqual(struct_before, struct_after)
        choices = construct.choice_set.all()
        choice1_name_after = choices[0].name_txt
        self.assertEqual(choice1_name_before, choice1_name_after)


    def test_check_integrity_resend_post(self):
        print("\n>>> test_check_integrity_resend_post() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_earlier = int(dt.datetime.now().timestamp()) + 3
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_earlier}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        time_later = int(dt.datetime.now().timestamp()) + 10
        request.POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "tr_1",
    "class": "Choice",
    "cells": {"class": "delete and", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "tr_2",
    "class": "Choice",
    "cells": { "class": "delete and", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  },
  "row_4": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_5": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}

        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 3)


    def test_check_integrity_wrong_post_2(self):
        print("\n>>> test_check_integrity_wrong_post_2() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_earlier = int(dt.datetime.now().timestamp()) - 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_earlier}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 0)


    def test_check_integrity_wrong_post_1(self):
        print("\n>>> test_check_integrity_wrong_post_1() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        class Request:
            method = "POST"
            POST = {"json_value":
'''
{
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 0)


    def test_check_integrity_wrong_resend_post(self):
        '''
            Passes timestamp check, but structure is wrong.
            This one should not break the construct's structure.
            We decide to fix the structure in such a way that
            new (strange) choices are just added to the construct.
        '''
        print("\n>>> test_check_integrity_wrong_resend_post() <<<")
        construct = Construct(title_text="Construct name")
        construct.save()
        time_earlier = int(dt.datetime.now().timestamp()) + 3
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_earlier}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify"
    }
  },
  "row_3": {
    "id": "",
    "class": "Choice",
    "cells": { "class": "", "name": "Bathtub silicon", "price": "£1.0", "quantity": "1.0",
      "units": "nr", "total_price": "£1.0", "assigned_to": "Somebody", "day_start": "May 9, 2023",
      "days": "1.0", "progress_bar": "5.00%", "progress": "5.0 %", "delete_action": "delete | modify"
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        time_later = int(dt.datetime.now().timestamp()) + 10
        post_json_line = json.loads(request.POST["json_value"])
        post_json_line["timestamp"] = str(time_later)
        request.POST["json_value"] = json.dumps(post_json_line)
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 5)


    def test_check_integrity_wrong_structure_2(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
                self.name_txt = str(ID) + "_name"
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in [10, 15, 23, 24, 25, 26, 44]]
        struc_dic = check_integrity(
            '''{
            "line_1":{"type":"Header2", "id":"House"},
            "line_2":{"type":"Choice", "id":"10"},
            "line_3":{"type":"Choice", "id":"15"},
            "line_4":{"type":"Header2", "id":"Shed"},
            "line_5":{"type":"Choice", "id":"23"},
            "line_6":{"type":"Choice", "id":"47"}
            }''', choices)
        self.assertEqual(len(struc_dic), 9)


class ClientSlugTests(TestCase):
    def test_access_client_view(self):
        c = Client()
        cons = make_test_construct("Client page view")
        cons.owner_name_text = "Mr. Ivan Ivanovich"
        cons.save()
        access_str = '/list/client/' + str(cons.slug_name)
        response = c.get(access_str)
        self.assertEqual(response.status_code, STATUS_CODE_OK)


    def test_updating_notes(self):
        construct = Construct(title_text="Construct name")
        construct.save()
        time_later = int(dt.datetime.now().timestamp()) + 10
        class Request:
            method = "POST"
            POST = {"json_value": "{" + f'"timestamp": "{time_later}",' + \
'''
  "row_1": {
    "id": "hd_0",
    "class": "Header2",
    "cells": {"class": "td_header_2", "name": "Bathroom", "price": "", "quantity": "", "units": "",
      "total_price": "", "assigned_to": "", "day_start": "delete | modify"
    }
  },
  "row_2": {
    "id": "",
    "class": "Choice",
    "cells": {"class": "", "name": "mirror", "price": "£ 1", "quantity": "1", "units": "nr",
      "total_price": "£ 1", "assigned_to": "Somebody", "day_start": "2023-05-09", "days": "1",
      "progress_bar": "0.0%", "progress": "0.0 %", "delete_action": "delete | modify",
      "notes": {"constructive_notes": "my con notes", "client_notes": "tricky_str"}
    }
  }
}
'''}
        request = Request()
        process_post(request, construct)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 2)
        json_val = json.loads(request.POST['json_value'])
        json_val['row_2']['id'] = 'tr_1'
        request.POST["json_value"] = json.dumps(json_val)
        request.POST["json_value"] = request.POST["json_value"].replace("tricky_str", "updated_str")
        c = Client()
        access_str = '/list/client/' + str(construct.slug_name)
        response = c.post(access_str, {"json_value": request.POST["json_value"]})
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        structure_str = construct.struct_json
        choices = construct.choice_set.all()
        struc_dict = check_integrity(structure_str, choices)
        self.assertIs(len(struc_dict), 2)
        self.assertEqual(choices[0].client_notes, 'updated_str')
