from django.test import TestCase, Client
from django.contrib.auth.models import User
import numpy as np
import datetime as dt
import json
from list.views import check_integrity,   \
                       is_yyyy_mm_dd,     \
                       is_month_day_year, \
                       create_choice,     \
                       update_choice,     \
                       process_post,      \
                       checkTimeStamp
from list.models import Construct, Choice, Invoice, Transaction

class ModelTests(TestCase):
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

    def test_login_page_list(self):
        c = Client()
        response = c.get('/list/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_login_page_detail(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
        self.assertEqual(response.status_code, 302)

    def test_login_page_flows(self):
        c = Client()
        cons = Construct()
        cons.save()
        response = c.get('/list/' + str(cons.id) +'/flows/')
        self.assertIs(response.url.find('accounts/login') >= 0, True)
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
        print('test_check_integrity_wrong_structure')
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in np.random.rand(10) * 100]
        struc_dic = check_integrity('{"line1":{"type":"Header2", "id":"House"}, "line2":{"type":"Choice", "id":"37"}}', choices)
        self.assertIs(len(struc_dic) == 0, True)


    def test_check_integrity_right_structure(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
        print('test_check_integrity_right_structure')
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in [10, 15, 23, 44]]
        struc_dic = check_integrity(
            '''{
            "line1":{"type":"Header2", "id":"House"},
            "line2":{"type":"Choice", "id":"10"},
            "line3":{"type":"Choice", "id":"15"},
            "line4":{"type":"Header2", "id":"Shed"},
            "line5":{"type":"Choice", "id":"23"},
            "line6":{"type":"Choice", "id":"44"}
            }''', choices)
        print('check_integrity_right_sturcture\n', struc_dic)
        self.assertIs(len(struc_dic) == 6, True)


    def test_process_post(self):
        print("\n>>> test_process_post() <<<")
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
        self.assertIs(len(struc_dict), 3)


    def test_check_integrity_wrong_structure_2(self):
        class LocalChoice:
            def __init__(self, ID):
                self.id = ID
                self.name_txt = str(ID) + "_name"
        print('test_check_integrity_right_structure_2')
        np.random.seed(0)
        choices = [LocalChoice(int(new_id)) for new_id in [10, 15, 23, 24, 25, 26, 44]]
        struc_dic = check_integrity(
            '''{
            "line1":{"type":"Header2", "id":"House"},
            "line2":{"type":"Choice", "id":"10"},
            "line3":{"type":"Choice", "id":"15"},
            "line4":{"type":"Header2", "id":"Shed"},
            "line5":{"type":"Choice", "id":"23"},
            "line6":{"type":"Choice", "id":"44"}
            }''', choices)
        print('check_integrity_right_sturcture\n', struc_dic)
        self.assertIs(len(struc_dic) == 0, True)
