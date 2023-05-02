from django.test import TestCase
import numpy as np
from list.views import check_integrity,   \
                       is_yyyy_mm_dd,     \
                       is_month_day_year, \
                       create_choice,     \
                       update_choice
from list.models import Construct, Choice

class ViewTests(TestCase):
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


    def test_update_choice_1(self):
        print("test_update_choice_1()")
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
        construct = Construct()
        construct.save()
        choice_id = create_choice(cell_data, construct)
        cells['units'] = 'sq. m.'
        ret = update_choice(choice_id, cell_data)
        self.assertIs(ret == choice_id, True)


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
