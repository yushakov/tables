from django.test import TestCase, Client
from list.models import User, \
                        Invoice,\
                        CLIENT_GROUP_NAME, \
                        WORKER_GROUP_NAME, \
                        StatusChain, Status
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from list.tests import make_test_construct
import json

STATUS_CODE_OK = 200
STATUS_CODE_REDIRECT = 302
STATUS_CODE_FORBIDDEN = 403

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
        workers_group.permissions.add(add_invoice_permission, view_invoice_permission)
        self.worker_user_2 = User.objects.create_user('worker2', 'worker@example.com', 'secret')
        self.worker_user_2.groups.add(workers_group)

        # client in the Clients group
        clients_group, _ = Group.objects.get_or_create(name=CLIENT_GROUP_NAME)
        content_type = ContentType.objects.get_for_model(Invoice)
        self.client_user_2 = User.objects.create_user('client2', 'client@example.com', 'secret')
        self.client_user_2.groups.add(clients_group)
    
    def test_index_redirect(self):
        c = Client()
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)
    
    def test_index_access_superuser(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_index_access_simple(self):
        c = Client()
        logged_in = c.login(username="simple", password="secret")
        self.assertTrue(logged_in)
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_slug_access_anonymous(self):
        c = Client()
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/slug/" + str(cons.slug_name))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_slug_access_anonymous_wrong_slug(self):
        c = Client()
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/slug/zzzz")
        self.assertEqual(response.status_code, 404)

    def test_index_access_worker(self):
        c = Client()
        logged_in = c.login(username="worker2", password="secret")
        self.assertTrue(logged_in)
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_index_access_client(self):
        c = Client()
        c.login(username="client2", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_REDIRECT)

    def test_get_choices_superuser(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/choices/?id=" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_get_choices_superuser_wrong_id(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/choices/?id=555")
        self.assertEqual(response.status_code, 404)

    def test_get_slug_choices_anonymous(self):
        c = Client()
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/slug_choices/?slug=" + cons.slug_name)
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_get_slug_choices_anonymous_wrong_slug(self):
        c = Client()
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/slug_choices/?slug=zzz")
        self.assertEqual(response.status_code, 404)

    def test_get_choices_worker(self):
        c = Client()
        logged_in = c.login(username="worker2", password="secret")
        self.assertTrue(logged_in)
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/choices/?id=" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_FORBIDDEN)

    def test_get_choices_client(self):
        c = Client()
        logged_in = c.login(username="client2", password="secret")
        self.assertTrue(logged_in)
        cons = make_test_construct('Test construct for session')
        response = c.get("/gantt/api/choices/?id=" + str(cons.id))
        self.assertEqual(response.status_code, STATUS_CODE_FORBIDDEN)
    
    def test_access_choices_update_superuser(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons = make_test_construct('Test construct for session')
        choices = cons.choice_set.all()
        data = {"choices": [{"id": str(choices[0].id),
                "plan_start_date": "2023-11-18",
                "plan_days_num": 9+3,
                "progress_percent_num": 82-12,
                "type": "task"}]}
        response = c.post("/gantt/api/choices_update/", data, content_type='application/json')
        self.assertEqual(response.status_code, STATUS_CODE_OK)
        choices = cons.choice_set.all()
        self.assertEqual(choices[0].plan_days_num, 12)
        self.assertEqual(choices[0].progress_percent_num, 70)

    def test_constructs_all(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons1 = make_test_construct('Test 1')
        cons2 = make_test_construct('Test 2')
        response = c.get("/gantt/constructs/all")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_constructs_no_cats_cat_1(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons1 = make_test_construct('Test 1')
        cons2 = make_test_construct('Test 2')
        response = c.get("/gantt/constructs/1")
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_constructs_cat_1(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons1 = make_test_construct('Test 1')
        cons2 = make_test_construct('Test 2')
        chain = StatusChain(name='Active')
        chain.save()
        status = Status(name='Ok')
        status.chain = chain
        status.save()
        for con in [cons1, cons2]:
            con.status = status
            con.save()
        response = c.get("/gantt/constructs/" + str(status.id))
        self.assertEqual(response.status_code, STATUS_CODE_OK)

    def test_constructs_cat_1_2(self):
        c = Client()
        c.login(username="yuran", password="secret")
        cons1 = make_test_construct('Test 1')
        cons2 = make_test_construct('Test 2')
        cons3 = make_test_construct('Test 3')
        chain1 = StatusChain(name='Active')
        chain1.save()
        chain2 = StatusChain(name='Sale')
        chain2.save()
        status1 = Status(name='Ok')
        status1.chain = chain1
        status1.save()
        status2 = Status(name='Deposit paid')
        status2.chain = chain2
        status2.save()
        for con in [cons1, cons2]:
            con.status = status1
            con.save()
        cons3.status = status2
        response = c.get(f"/gantt/constructs/{status1.id},{status2.id}")
        self.assertEqual(response.status_code, STATUS_CODE_OK)