import os
from django.contrib import admin
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.files.base import ContentFile
import logging
import json
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
import difflib

logger = logging.getLogger('django')

percent_valid = [MinValueValidator(0), MaxValueValidator(100)] 
coeff_valid = [MinValueValidator(0.0), MaxValueValidator(1.0)] 
phone_valid = [RegexValidator(regex=r'^[+0-9]*$', message='Only numbers and +')]


def total_model_stat():
    import list.models as lm
    out = {}
    for attr in dir(lm):
        obj = getattr(lm, attr)
        if type(obj) != type(lm.Construct): continue
        obj_count = len(obj.objects.all())
        print(attr, ': ', obj_count)
        out[attr] = obj_count
    return out


class Client(models.Model):
    name = models.CharField(max_length=100)
    contact_info = models.TextField()

    def __str__(self):
        return self.name


class Construct(models.Model):
    title_text = models.CharField(max_length=200)
    listed_date = models.DateTimeField('date listed', default=timezone.now)
    last_save_date = models.DateTimeField('last save', default=timezone.now)
    address_text = models.CharField(max_length=500)
    email_text = models.EmailField(default='email@domain.com')
    phone_text = models.CharField(max_length=200, validators=phone_valid, default='07770777')
    owner_name_text = models.CharField(max_length=200)
    assigned_to = models.CharField(max_length=800, default='Some Team')
    overall_progress_percent_num = models.FloatField('progress', default=0.0, validators=percent_valid)
    vat_percent_num = models.FloatField(validators=percent_valid, default='5')
    company_profit_percent_num = models.FloatField(validators=percent_valid, default='15')
    owner_profit_coeff = models.FloatField(validators=coeff_valid, default='0.13')
    paid_num = models.FloatField(default='0')
    struct_json = models.TextField(default='{}')
    
    def __str__(self):
        return self.title_text

    def shallow_copy(self):
        return Construct(
                title_text = self.title_text,
                listed_date = self.listed_date,
                last_save_date = self.last_save_date,
                address_text = self.address_text,
                email_text = self.email_text,
                phone_text = self.phone_text,
                owner_name_text = self.owner_name_text,
                assigned_to = self.assigned_to,
                overall_progress_percent_num = self.overall_progress_percent_num,
                vat_percent_num = self.vat_percent_num,
                company_profit_percent_num = self.company_profit_percent_num,
                owner_profit_coeff = self.owner_profit_coeff,
                paid_num = self.paid_num,
                struct_json = self.struct_json)

    def save(self, *args, **kwargs):
        delta_to_make_construct_a_bit_younger = timedelta(seconds=2)
        self.last_save_date = timezone.now() + delta_to_make_construct_a_bit_younger
        super(Construct, self).save(*args, **kwargs)

    def copy(self, new_title):
        if len(Construct.objects.filter(title_text=new_title.strip())) > 0:
            return None
        new_construct = Construct(title_text=new_title,
                vat_percent_num = self.vat_percent_num,
                company_profit_percent_num = self.company_profit_percent_num,
                owner_profit_coeff = self.owner_profit_coeff)
        new_construct.save()
        json_dic = json.loads(self.struct_json)
        choices = self.choice_set.all()
        for line in json_dic.keys():
            if json_dic[line]['type'] != 'Choice': continue
            ch = choices.get(id=json_dic[line]['id'])
            new_choice = ch.copy(new_construct)
            json_dic[line]['id'] = str(new_choice.id)
        new_construct.struct_json = json.dumps(json_dic)
        new_construct.save()
        return new_construct

    def history_dump(self, user_id):
        user = User.objects.get(id = user_id)
        fname = self.last_save_date.strftime('%Y-%m-%d_%H-%M-%S_%f') +\
            '_user_' + str(user) + '_construct_' + str(self.id) + '.json'
        filepath = os.path.join(settings.BASE_DIR, 'history', fname)
        self.export_to_json(filepath)
        record = HistoryRecord(construct=self,
            user_id   = int(user_id),
            user_name = user,
            file_path = filepath)
        record.save()
        return filepath

    def get_history_records(self, limit=None):
        records = self.historyrecord_set.all()
        if limit:
            return records[:limit]
        return records

    def get_last_history_record(self):
        pth = os.path.join(settings.BASE_DIR, 'history')
        records = os.listdir(pth)
        if len(records) > 0:
            with open(pth + '/' + records[0], 'r') as rec:
                return rec.read()
        return ''

    def export_to_json(self, fname):
        construct = self
        choices = Choice.objects.filter(construct__id=construct.id)
        transactions = Transaction.objects.filter(construct__id=construct.id)
        invoices = Invoice.objects.filter(construct__id=construct.id)
        invoice_transactions = InvoiceTransaction.objects.filter(construct__id=construct.id)
        history_records = self.historyrecord_set.all()
        data = serializers.serialize('json', [self, *choices, *transactions,
                                              *invoices, *invoice_transactions,
                                              *history_records],
                   use_natural_foreign_keys=True, use_natural_primary_keys=True)
        with open(fname, 'w') as outfile:
            outfile.write(data)

    def get_stat(self):
        """
        To check which classes are linked with the Construct:
            grep -E "(^class|ForeignKey\(Construct)" list/models.py
        As of now (August 13, 2023):
            class HistoryRecord(models.Model):
                construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
            class Choice(models.Model):
                construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
            class Transaction(models.Model):
                construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
            class Invoice(models.Model):
                construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
            class InvoiceTransaction(models.Model):
                construct = models.ForeignKey(Construct, on_delete=models.CASCADE, null=True, blank=True)
        """
        out = {}
        choices = self.choice_set.all()
        transactions = self.transaction_set.all()
        invoices = self.invoice_set.all()
        invoice_transactions = self.invoicetransaction_set.all()
        out['HistoryRecord'] = len(self.historyrecord_set.all())
        out['Choice'] = len(choices)
        out['Transaction'] = len(transactions)
        out['Invoice'] = len(invoices)
        out['InvoiceTransaction'] = len(invoice_transactions)

        def get_total(items, func=lambda x: x.amount):
            total_amount = 0.0
            for item in items:
                total_amount += float(func(item))
            return round(total_amount)

        out['choices_total'] = get_total(choices, lambda x: x.quantity_num * x.price_num)
        out['transactions_total'] = get_total(transactions)
        out['invoices_total'] = get_total(invoices)
        out['inv_tra_total'] = get_total(invoice_transactions, lambda x: x.invoice.amount)
        return out


    def safe_import_from_json(fname):
        with open(fname, 'r') as data_file:
            construct = None
            invoices = {}
            transactions = {}
            choices = {}
            invtra_objects = []
            for obj in serializers.deserialize("json", data_file):
                if type(obj.object) == Construct:
                    new_title = 'Imported: ' + obj.object.title_text
                    print('Construct: ', new_title)
                    construct = obj.object.shallow_copy()
                    construct.title_text = new_title
                    construct.save()
                elif type(obj.object) == Choice:
                    print('Choice: ', obj.object.name_txt)
                    choice = obj.object.shallow_copy(construct)
                    choice.save()
                    choices[int(obj.object.id)] = choice.id
                elif type(obj.object) == Invoice:
                    print('Invoice', obj.object.id)
                    invoice = obj.object.shallow_copy(construct)
                    invoice.save()
                    invoices[int(obj.object.id)] = invoice
                elif type(obj.object) == Transaction:
                    print('Transaction: ', obj.object.id)
                    transaction = obj.object.shallow_copy(construct)
                    transaction.save()
                    transactions[int(obj.object.id)] = transaction
                elif type(obj.object) == InvoiceTransaction:
                    print('InvoiceTransaction: ', obj.object.id)
                    invtra_objects.append(obj.object)
                elif type(obj.object) == HistoryRecord:
                    print('HistoryRecord: ', obj.object.id)
                    history_record = obj.object.shallow_copy(construct)
                    history_record.save()
                else:
                    print('Unknown Type: ', type(obj.object))
            # process sruct_json
            struct_dic = json.loads(construct.struct_json)
            for line in struct_dic.keys():
                if struct_dic[line]['type'] == 'Choice':
                    struct_dic[line]['id'] = str(choices[int(struct_dic[line]['id'])])
            construct.struct_json = json.dumps(struct_dic)
            construct.save()
            # process InvoiceTransaction connections
            for invtra in invtra_objects:
                invoice = invoices[invtra.invoice_id]
                transac = transactions[invtra.transaction_id]
                invoice_transaction = InvoiceTransaction(construct=construct,
                                                         invoice=invoice,
                                                         transaction=transac)
                invoice_transaction.save()
            return construct

    @admin.display(description='Progress')
    def overall_progress(self):
        return f"{self.overall_progress_percent_num :.2f} %" 

    @admin.display
    def email(self):
        return f"{self.email_text}"

    @admin.display(description='To do')
    def goto(self):
        return format_html("<a href='/list/{}'>view</a>", self.id)

    def balance(self):
        transactions = self.transaction_set.all()
        income  = sum([ta.amount for ta in transactions if ta.transaction_type == ta.INCOMING])
        outcome = sum([ta.amount for ta in transactions if ta.transaction_type == ta.OUTGOING])
        return income - outcome

    def debt(self):
        invoices = self.invoice_set.all()
        income  = sum([iv.amount for iv in invoices if iv.invoice_type == Transaction.INCOMING and iv.status != Invoice.PAID])
        outcome = sum([iv.amount for iv in invoices if iv.invoice_type == Transaction.OUTGOING and iv.status != Invoice.PAID])
        return income - outcome

    @property
    def invoices_to_pay(self):
        invoices = self.invoice_set.filter(invoice_type=Transaction.OUTGOING, status=Invoice.UNPAID)
        if invoices is None: return 0.0
        return round(sum([iv.amount for iv in invoices]))

    @property
    def invoices_pending_pay(self):
        invoices = self.invoice_set.filter(invoice_type=Transaction.INCOMING, status=Invoice.UNPAID)
        if invoices is None: return 0.0
        return round(sum([iv.amount for iv in invoices]))

    def income(self):
        in_transactions = self.transaction_set.filter(transaction_type = Transaction.INCOMING)
        if in_transactions is None: return 0.0
        income = sum([float(ta.amount) for ta in in_transactions])
        return income

    def salaries(self):
        transactions = self.transaction_set.filter(transaction_type=Transaction.OUTGOING, details_txt__icontains='salary')
        if transactions is None: return 0.0
        summ = sum([float(ta.amount) for ta in transactions])
        return summ

    def outcome(self):
        out_transactions = self.transaction_set.filter(transaction_type = Transaction.OUTGOING)
        if out_transactions is None: return 0.0
        outcome = sum([float(ta.amount) for ta in out_transactions])
        return outcome

    def expenses(self):
        return self.outcome() - self.salaries()

    @property
    def round_salaries(self):
        return round(self.salaries())

    @property
    def company_profit(self):
        return round(self.income() - self.outcome())

    @property
    def owner_profit(self):
        return round(self.withOutVat(self.income()) * self.owner_profit_coeff)

    @property
    def salaries_part(self):
        # Income - VAT - Owner Profit - Outcome
        return round(self.withOutVat(self.income()) - self.owner_profit - self.outcome())

    @property
    def company_profit_percent(self):
        income = self.income()
        if income < 1.e-5:
            return 0.0
        return 100. * float(self.company_profit) / self.income()

    @property
    def round_expenses(self):
        return round(self.expenses())

    @property
    def round_income(self):
        return round(self.income())

    @property
    def round_outcome(self):
        return round(self.outcome())

    @property
    def progress_minus_income(self):
        return round(self.full_progress_cost - self.income())

    def progress_cost(self):
        choices = self.choice_set.all()
        if choices is None: return 0.0
        cost = 0.0
        for ch in choices:
            price = ch.quantity_num * ch.price_num * ch.progress_percent_num * 0.01
            cost += price
        return cost

    def overall_progress_percent(self):
        choices = self.choice_set.all()
        if choices is None: return 0.0
        total_cost, progress_cost = 0.0, 0.0
        for ch in choices:
            ch_price = ch.quantity_num * ch.price_num
            total_cost += ch_price
            progress_cost += ch_price * ch.progress_percent_num * 0.01
        if total_cost > 1.e-5:
            self.overall_progress_percent_num = 100.0 * progress_cost / total_cost
            return self.overall_progress_percent_num
        else:
            return 0.0

    def withCompanyProfit(self, value):
        return value * (1.0 + 0.01 * self.company_profit_percent_num)

    def withVat(self, value):
        return value * (1.0 + 0.01 * self.vat_percent_num)

    def withOutVat(self, value):
        return value / (1.0 + 0.01 * self.vat_percent_num)

    @property
    def full_cost(self):
        choices = self.choice_set.all()
        choices_cost = sum([ch.price_num * ch.quantity_num for ch in choices])
        return round(self.withVat(self.withCompanyProfit(choices_cost)))

    @property
    def full_progress_cost(self):
        return round(self.withVat(self.withCompanyProfit(self.progress_cost())))


class HistoryRecord(models.Model):
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    user_id = models.IntegerField(default='0')
    user_name = models.CharField(max_length=200, default='')
    file_path = models.CharField(max_length=700, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '"' + self.construct.title_text[:10] + '" from ' + \
               str(self.created_at.strftime('%Y.%m.%d %H:%M:%S')) + ' by "' + \
               self.user_name + '"'

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def shallow_copy(self, construct):
        return HistoryRecord(construct=construct,
                             user_id=self.user_id,
                             user_name=self.user_name,
                             file_path=self.file_path,
                             created_at=self.created_at)

    def get_record(record_id):
        try:
            record = HistoryRecord.objects.get(id=record_id)
            with open(record.file_path, 'r', encoding='utf-8') as file:
                json_dic = json.loads(file.read())
                return json.dumps(json_dic, indent=2, ensure_ascii=False)
            return "Coundn't open the file"
        except:
            return f'No record with id: {record_id}'

    def get_diff(record_id1, record_id2):
        text1 = HistoryRecord.get_record(record_id1)
        text2 = HistoryRecord.get_record(record_id2)
        lst1  = text1.split('\n')
        lst2  = text2.split('\n')
        diff_lines = [l for l in difflib.unified_diff(lst1, lst2)]
        new_lines = []
        for l in diff_lines:
            if l.find('"struct_json":') >= 0: continue
            if l.startswith('+'):
                new_lines.append("<p style='color: green'>" + l + "</p>\n")
            elif l.startswith('-'):
                new_lines.append("<p style='color: red'>" + l + "</p>\n")
            else:
                new_lines.append(l + "<br>\n")
        out = ''.join([l for l in new_lines])
        return out


class Worker(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=200, validators=phone_valid)
    
    def __str__(self):
        return self.name


def instances_are_equal(instance1, instance2, fields=None):
    if fields is None:
        fields = [f.name for f in instance1._meta.fields]
    for field in fields:
        if getattr(instance1, field) != getattr(instance2, field):
            logger.debug(f'"{getattr(instance1, field)}" != "{getattr(instance2, field)}"')
            return False
    return True


class Choice(models.Model):
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    #workers = models.ManyToManyField(Worker, default=None)
    workers = models.CharField(max_length=800, default='Somebody')
    name_txt = models.CharField(max_length=200)
    notes_txt = models.TextField(default='-')
    constructive_notes = models.TextField(default='-')
    client_notes = models.TextField(default='-')
    quantity_num = models.FloatField(default='1')
    units_of_measure_text = models.CharField(max_length=100, default='-')
    price_num = models.FloatField()
    progress_percent_num = models.FloatField(validators=percent_valid, default='0')
    plan_start_date = models.DateField(default=timezone.now)
    plan_days_num = models.FloatField()
    actual_start_date = models.DateField(default=timezone.now)
    actual_end_date = models.DateField(default=timezone.now)

    def shallow_copy(self, construct):
        return Choice(construct=construct,
                workers = self.workers,
                name_txt = self.name_txt,
                notes_txt = self.notes_txt,
                constructive_notes = self.constructive_notes,
                client_notes = self.client_notes,
                quantity_num = self.quantity_num,
                units_of_measure_text = self.units_of_measure_text,
                price_num = self.price_num,
                progress_percent_num = self.progress_percent_num,
                plan_start_date = self.plan_start_date,
                plan_days_num = self.plan_days_num,
                actual_start_date = self.actual_start_date,
                actual_end_date = self.actual_end_date)

    def copy(self, construct):
        new_choice = Choice(construct=construct,
                workers = self.workers,
                name_txt = self.name_txt,
                notes_txt = self.notes_txt,
                constructive_notes = self.constructive_notes,
                client_notes = self.client_notes,
                quantity_num = self.quantity_num,
                units_of_measure_text = self.units_of_measure_text,
                price_num = self.price_num,
                progress_percent_num = 0,
                plan_start_date = self.plan_start_date,
                plan_days_num = self.plan_days_num)
        new_choice.save()
        return new_choice

    def __str__(self):
        maxNameLen = 70
        out_name = self.name_txt
        if len(out_name) > maxNameLen:
            out_name = out_name[:maxNameLen] + "..."
        return f'{self.id}: ' + out_name + f' ({self.construct})'

    @admin.display(description="Name", ordering="name_txt")
    def get_name(self):
        return f"{self.name_txt}"

    @admin.display(description="Progress, %", ordering="progress_percent_num")
    def get_progress(self):
        return f"{self.progress_percent_num}"

    def save(self, *args, **kwargs):
        if self.pk:  # pk will be None for a new instance
            existing_instance = Choice.objects.get(pk=self.pk)
            if instances_are_equal(existing_instance, self):
                logger.debug('Nothing to update, instances are equal...')
                return
        # save(), if the instance is new or changed
        if self.pk:
            logger.info(f'send {self.pk} to DB')
        else:
            logger.info(f'New "{self.name_txt[:50]}" in DB')
        self.construct.save()
        super(Choice, self).save(*args, **kwargs)


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


def get_id(model_class):
    '''
        Generate an ID string basing on the max ID of the DB entries.
    '''
    OutLen = 17
    max_id = model_class.objects.aggregate(models.Max('id'))['id__max']
    if max_id is None:
        max_id = 0
    return str(uuid.uuid3(uuid.NAMESPACE_OID, str(max_id+1))).replace('-','').upper()[:OutLen]


def getConstructAndMaxId(construct_id, model_class):
    if construct_id <= 0: return '0-0-0'
    objects = model_class.objects.filter(construct__id=construct_id)
    max_id, obj_count = 0, 0
    if len(objects) > 0:
        max_id, obj_count = max([obj.id for obj in objects]), len(objects)
    return f'{construct_id}-{obj_count+1}-{max_id+1}'


def empty_image():
    return ContentFile(b"<img>", name="default.jpg")


class Transaction(models.Model):
    INCOMING = 'IN'
    OUTGOING = 'OUT'

    TYPES = [
        (INCOMING, 'Incoming'),
        (OUTGOING, 'Outgoing'),
    ]

    from_txt = models.CharField(max_length=200, default='')
    to_txt = models.CharField(max_length=200, default='')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(max_length=3, choices=TYPES)
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    receipt_number = models.CharField(max_length=100, default="000000")
    details_txt = models.TextField(default='-')
    photo = models.ImageField(upload_to="receipts/%Y/%m/%d", default=empty_image)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def shallow_copy(self, construct):
        return Transaction(construct=construct,
                from_txt         = self.from_txt,
                to_txt           = self.to_txt,
                amount           = self.amount,
                transaction_type = self.transaction_type,
                date             = self.date,
                receipt_number   = self.receipt_number,
                details_txt      = self.details_txt,
                photo            = self.photo,
                created_at       = self.created_at)

    def __str__(self):
        return f'Tra:{self.receipt_number}, From: {self.from_txt}, ' + \
               f'To: {self.to_txt}, ' + \
               f'Date: {self.date}, £ {self.amount}'

    def get_absolute_url(self):
        return f"/list/transaction/{self.id}"

    @admin.display(description='Project')
    def within(self):
        return f"{self.construct.title_text}"

    @admin.display(description='From')
    def get_from_txt(self):
        return f"{self.from_txt}"

    @admin.display(description='To')
    def get_to_txt(self):
        return f"{self.to_txt}"

    @admin.display(description="Number")
    def number_link(self):
        return format_html("<a href='/list/transaction/{}'>{}</a>", self.id, self.receipt_number)

    @admin.display(description="Type")
    def get_type(self):
        return f"{self.transaction_type}"

    def add_as_on_page(construct, _from, _to, amount, inout, date, number, details):
        tra = Transaction(construct = construct,
                from_txt = _from,
                to_txt = _to,
                amount = amount,
                transaction_type = inout,
                date = date,
                receipt_number = number,
                details_txt = details)
        tra.save()

    def add(construct, amount, date=None, direction=None, number='000000', details='-'):
        transaction = Transaction()
        transaction.construct = construct
        transaction.amount = amount
        transaction.details_txt = details
        if date is None:
            transaction.date = timezone.now()
        else:
            transaction.date = date
        if direction is None or direction == 'in':
            transaction.transaction_type = Transaction.INCOMING
        elif direction == 'out':
            transaction.transaction_type = Transaction.OUTGOING
        else:
            logger.error(f"ERROR: unsupported direction '{direction}'")
            return None
        transaction.photo = ContentFile(b"<img>", name="default.jpg")
        transaction.save()
        return transaction

    def save(self, *args, **kwargs):
        logger.info(f"Transaction.save(): {self}")
        logger.info(self.photo)
        super(Transaction, self).save(*args, **kwargs)


class Invoice(models.Model):
    PAID = 'Paid'
    UNPAID = 'Unpaid'
    STATUS = [
        (PAID, 'Paid'),
        (UNPAID, 'Unpaid')
    ]

    def get_id():
        return get_id(Invoice)

    number = models.CharField(max_length=100, default=get_id)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    invoice_type = models.CharField(max_length=3, choices=Transaction.TYPES, default=Transaction.INCOMING)
    status = models.CharField(max_length=6, choices=STATUS, default=UNPAID)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(default=timezone.now)
    seller = models.CharField(max_length=100)
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    transactions = models.ManyToManyField(Transaction, through='InvoiceTransaction')
    photo = models.ImageField(upload_to="invoices/%Y/%m/%d", default=empty_image)
    created_at = models.DateTimeField(auto_now_add=True)
    details_txt = models.TextField(default='-')

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def shallow_copy(self, construct):
        return Invoice(construct=construct,
                number       = self.number,
                amount       = self.amount,
                invoice_type = self.invoice_type,
                status       = self.status,
                issue_date   = self.issue_date,
                due_date     = self.due_date,
                seller       = self.seller,
                #transactions = ..., ### don't copy Many-to-Many in shallow_copy() ###
                photo        = self.photo,
                created_at   = self.created_at,
                details_txt  = self.details_txt)

    def __str__(self):
        return f"Inv:{self.number};({self.construct.title_text[:10]}...) from: {self.seller}; " + \
               f"date: {self.issue_date}; £{self.amount} {self.invoice_type}"

    def get_absolute_url(self):
        return f"/list/invoice/{self.id}"

    @admin.display(description="Project")
    def within(self):
        return f"{self.construct.title_text}"

    @admin.display(description="Number")
    def number_link(self):
        return format_html("<a href='/list/invoice/{}'>{}</a>", self.id, self.number)

    def get_transactions(self):
        return self.transactions.all()

    def add(construct, seller_name, amount, direction=None, issued=None, due=None, status=None):
        invoice = Invoice()
        invoice.seller = seller_name
        invoice.amount = amount 
        if status is None or status == 'unpaid':
            invoice.status = Invoice.UNPAID
        else:
            invoice.status = Invoice.PAID
        if direction is None or direction == 'in':
            invoice.invoice_type = Transaction.INCOMING
        elif direction == 'out':
            invoice.invoice_type = Transaction.OUTGOING
        else:
            logger.error(f"ERROR: unsupported direction '{direction}'")
            return None
        if issued is None:
            invoice.issue_date = timezone.now()
        else:
            invoice.issue_date = issued
        if due is None:
            invoice.due_date = timezone.now()
        else:
            invoice.due_date = due
        invoice.construct = construct
        invoice.photo = ContentFile(b"<img>", name="default.jpg")
        invoice.save()
        return invoice

    def save(self, *args, **kwargs):
        if self.id is not None:
            for ta in self.transactions.all():
                if f"{ta.transaction_type}" != f"{self.invoice_type}":
                    raise Exception("ERROR: transactions must be of the same type (IN or OUT) as the corresponding invoice.")
        logger.info(f'Invoice.save(): {self}')
        super(Invoice, self).save(*args, **kwargs)


class InvoiceTransaction(models.Model):
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE, null=True, blank=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    #paid_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('invoice', 'transaction')

    def __str__(self):
        return f'{self.invoice} - {self.transaction}'

