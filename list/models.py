from django.contrib import admin
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.files.base import ContentFile

percent_valid = [MinValueValidator(0), MaxValueValidator(100)] 
phone_valid = [RegexValidator(regex=r'^[+0-9]*$', message='Only numbers and +')]


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
    paid_num = models.FloatField(default='0')
    struct_json = models.TextField(default='{}')
    
    def __str__(self):
        return self.title_text

    def save(self, *args, **kwargs):
        delta_to_make_construct_a_bit_younger = timedelta(seconds=2)
        self.last_save_date = timezone.now() + delta_to_make_construct_a_bit_younger
        super(Construct, self).save(*args, **kwargs)

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

    def income(self):
        in_transactions = self.transaction_set.filter(transaction_type = Transaction.INCOMING)
        income = sum([float(ta.amount) for ta in in_transactions])
        return income

    def progress_cost(self):
        choices = self.choice_set.all()
        cost = 0.0
        for ch in choices:
            price = ch.quantity_num * ch.price_num * ch.progress_percent_num * 0.01
            cost += price
        return cost


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
            print(f'"{getattr(instance1, field)}" != "{getattr(instance2, field)}"')
            return False
    return True


class Choice(models.Model):
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    #workers = models.ManyToManyField(Worker, default=None)
    workers = models.CharField(max_length=800, default='Somebody')
    name_txt = models.CharField(max_length=200)
    notes_txt = models.TextField(default='-')
    quantity_num = models.FloatField(default='1')
    units_of_measure_text = models.CharField(max_length=100, default='-')
    price_num = models.FloatField()
    progress_percent_num = models.FloatField(validators=percent_valid, default='0')
    plan_start_date = models.DateField(default=timezone.now)
    plan_days_num = models.FloatField()
    actual_start_date = models.DateField(default=timezone.now)
    actual_end_date = models.DateField(default=timezone.now)

    def __str__(self):
        maxNameLen = 70
        out_name = self.name_txt
        if len(out_name) > maxNameLen:
            out_name = out_name[:maxNameLen] + "..."
        return f'{self.id}: ' + out_name + f' ({self.construct})'

    def save(self, *args, **kwargs):
        if self.pk:  # pk will be None for a new instance
            existing_instance = Choice.objects.get(pk=self.pk)
            if instances_are_equal(existing_instance, self):
                print('Nothing to update, instances are equal...')
                return
        # save(), if the instance is new or changed
        if self.pk:
            print(f'send {self.pk} to DB')
        else:
            print(f'New "{self.name_txt[:50]}" in DB')
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
    photo = models.ImageField(upload_to="receipts/%Y/%m/%d", default=ContentFile(b"<img>", name="default.jpg"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def __str__(self):
        return f'Tra:{self.receipt_number}, From: {self.from_txt}, ' + \
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

    def add(construct, amount, date=None, direction=None, number='000000'):
        transaction = Transaction()
        transaction.construct = construct
        transaction.amount = amount
        if date is None:
            transaction.date = timezone.now()
        else:
            transaction.date = date
        if direction is None or direction == 'in':
            transaction.transaction_type = Transaction.INCOMING
        elif direction == 'out':
            transaction.transaction_type = Transaction.OUTGOING
        else:
            print(f"ERROR: unsupported direction '{direction}'")
            return None
        transaction.photo = ContentFile(b"<img>", name="default.jpg")
        transaction.save()
        return transaction


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
    issue_date = models.DateField()
    due_date = models.DateField()
    seller = models.CharField(max_length=100)
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    transactions = models.ManyToManyField(Transaction, through='InvoiceTransaction')
    photo = models.ImageField(upload_to="invoices/%Y/%m/%d", default=ContentFile(b"<img>", name="default.jpg"))

    def __str__(self):
        return f"Inv:{self.number};({self.construct.title_text[:10]}...) from: {self.seller}; " + \
               f"date: {self.issue_date}; £{self.amount} {self.invoice_type}"

    @admin.display(description="Project")
    def within(self):
        return f"{self.construct.title_text}"

    @admin.display(description="Number")
    def number_link(self):
        return format_html("<a href='/list/invoice/{}'>{}</a>", self.id, self.number)

    def get_transactions(self):
        return self.transactions.all()

    def add(construct, seller_name, amount, direction=None, issued=None, due=None):
        invoice = Invoice()
        invoice.seller = seller_name
        invoice.amount = amount 
        if direction is None or direction == 'in':
            invoice.invoice_type = Transaction.INCOMING
        elif direction == 'out':
            invoice.invoice_type = Transaction.OUTGOING
        else:
            print(f"ERROR: unsupported direction '{direction}'")
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
        super(Invoice, self).save(*args, **kwargs)


class InvoiceTransaction(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    #paid_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('invoice', 'transaction')

    def __str__(self):
        return f'{self.invoice} - {self.transaction}'

