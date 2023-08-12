from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User, Permission
import numpy as np
import datetime as dt
import json
from list.views import check_integrity,   \
                       is_yyyy_mm_dd,     \
                       is_month_day_year, \
                       create_choice,     \
                       update_choice,     \
                       process_post,      \
                       checkTimeStamp,    \
                       fix_structure
from list.models import Construct, \
                        Choice, \
                        Invoice, \
                        Transaction, \
                        InvoiceTransaction, \
                        HistoryRecord, \
                        getConstructAndMaxId
import os


STATUS_CODE_OK = 200
STATUS_CODE_REDIRECT = 302

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

def make_test_construct(construct_name = 'Some test Construct'):
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
        self.assertEqual(tpl1, (1,3))
        self.assertEqual(tpl2, (2,4))
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
        Construct.import_from_json(fname)
        cons = Construct.objects.all()
        self.assertEqual(cons[0].title_text, construct_name)
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
        Construct.import_from_json(fname)
        cons = Construct.objects.all()
        self.assertEqual(cons[0].title_text, construct_name)
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
        self.assertIs(230.0 - 1.e-10 < float(income) < 230.0 + 1.e-10, True)

    def test_construct_debt(self):
        construct = Construct()
        construct.save()
        iv1 = Invoice.add(construct, "John", 100.0)
        iv2 = Invoice.add(construct, "Paul", 130.0)
        iv3 = Invoice.add(construct, "George", 50.0, direction='out')
        iv4 = Invoice.add(construct, "Ringo", 75.0, direction='out')
        construct.invoice_set.add(iv1, iv2, iv3, iv4)
        debt = construct.debt()
        self.assertIs(105.0 - 1.e-10 < float(debt) < 105.0 + 1.e-10, True)

    def test_construct_balance(self):
        construct = Construct()
        construct.save()
        ta1 = Transaction.add(construct, 100.0)
        ta2 = Transaction.add(construct, 130.0)
        ta3 = Transaction.add(construct, 50.0, direction='out')
        ta4 = Transaction.add(construct, 75.0, direction='out')
        construct.transaction_set.add(ta1, ta2, ta3, ta4)
        balance = construct.balance()
        self.assertIs(105.0 - 1.e-10 < float(balance) < 105.0 + 1.e-10, True)

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


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='yuran', password='secret', email='yuran@domain.com')
        self.simple_user = User(username='simple', password='secret', email='simple@domain.com')
        self.simple_user.save()
        self.client_user = User.objects.create_user(username='client',
                password='secret',
                email='client@domain.com')
        permission = Permission.objects.get(codename='view_construct')
        self.client_user.user_permissions.add(permission)

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
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(updated_date - timezone.now(), timedelta(days=1), delta=timedelta(seconds=5))

    def test_session_extension_on_client_page(self):
        c = Client()
        c.login(username="client", password="secret")
        cons = make_test_construct('Test construct for the client session')
        session = c.session
        session['key'] = 'value'
        one_hour = 60 * 60
        session.set_expiry(one_hour)
        session.save()
        response = c.get("/list/" + str(cons.id) + '/client/')
        session = c.session
        updated_date = session.get_expiry_date()
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(updated_date - timezone.now(), timedelta(days=1), delta=timedelta(seconds=5))

    def test_login_page_list(self):
        c = Client()
        response = c.get('/list/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

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

    def test_login_page_client_view(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/client/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_login_page_flows(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/flows/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_login_page_transactions(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_transactions_page_accessed(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertEqual(response.status_code, 200)

    def test_transactions_page_no_access(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/transactions/')
        self.assertEqual(response.status_code, 302)

    def test_login_page_gantt(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/gantt/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_call_flows_page(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, 200)

    def test_call_flows_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/flows/")
        self.assertEqual(response.status_code, 302)

    def test_call_gantt_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/gantt/")
        self.assertEqual(response.status_code, 302)

    def test_call_client_page_simple_user(self):
        c = Client()
        c.login(username="simple", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/client/")
        self.assertEqual(response.status_code, 302)

    def test_view_invoice(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        invs = Invoice.objects.all()
        inv = invs[0]
        inv.details_txt = 'Description on this invoice'
        inv.save()
        response = c.get("/list/invoice/" + str(inv.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_view_transaction(self):
        c = Client()
        c.login(username="yuran", password="secret")
        construct = make_test_construct('Test construct')
        tas = Transaction.objects.all()
        ta = tas[0]
        ta.details_txt = 'Description on this transaction'
        ta.save()
        response = c.get("/list/transaction/" + str(ta.id) + "/")
        self.assertEqual(response.status_code, 200)

    def test_call_client_page_client(self):
        c = Client()
        c.login(username="client", password="secret")
        cons = Construct()
        cons.save()
        response = c.get("/list/" + str(cons.id) + "/client/")
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 200)

    def test_open_transaction_submit_form(self):
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/")
        self.assertEqual(response.status_code, 200)

    def test_open_transaction_submit_form_populated(self):
        construct = Construct()
        construct.save()
        c = Client()
        c.login(username="yuran", password="secret")
        response = c.get("/list/transaction/submit/?construct=1&amount=100&invoice=29&type=IN")
        self.assertEqual(response.status_code, 200)

    def test_login_transaction_submit_form(self):
        c = Client()
        response = c.get("/list/transaction/submit/")
        self.assertEqual(response.status_code, 302)

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
        self.assertEqual(response.status_code, 302)
        
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
        self.assertEqual(response.status_code, 302)
        
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
        self.assertEqual(response.status_code, 302)

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
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 302)

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

    def test_modify_invoice_get(self):
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
        response = c.get(f"/list/invoice/{invoice.id}/modify/")
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        
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
        self.assertEqual(response.status_code, 302)
        
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
        print("test_update_choice_no_update()")
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
        print("test_update_choice()")
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


    def test_is_yyyy_mm_dd_1(self):
        print('test_is_yyyy_mm_dd_1')
        date = "2021-01-20"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, True)


    def test_is_yyyy_mm_dd_2(self):
        print('test_is_yyyy_mm_dd_2')
        date = "21-01-20"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, False)


    def test_is_yyyy_mm_dd_3(self):
        print('test_is_yyyy_mm_dd_3')
        date = "January 10, 2021"
        ret = is_yyyy_mm_dd(date)
        self.assertIs(ret, False)


    def test_is_month_day_year_1(self):
        print('test_is_month_day_year_1')
        date = "January 10, 2021"
        ret = is_month_day_year(date)
        self.assertIs(ret, True)

    
    def test_is_month_day_year_2(self):
        print('test_is_month_day_year_2')
        date = "Jan 10, 2021"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)

    
    def test_is_month_day_year_3(self):
        print('test_is_month_day_year_3')
        date = "January 10, 21"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)

    
    def test_is_month_day_year_4(self):
        print('test_is_month_day_year_4')
        date = "January     10, 21"
        ret = is_month_day_year(date)
        self.assertIs(ret, False)

    
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
