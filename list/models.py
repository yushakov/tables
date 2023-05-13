from django.contrib import admin
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

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


class Transaction(models.Model):
    INCOMING = 'IN'
    OUTGOING = 'OUT'

    TRANSACTION_TYPES = [
        (INCOMING, 'Incoming'),
        (OUTGOING, 'Outgoing'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f'{self.transaction_type} - {self.amount}'


class Invoice(models.Model):
    number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    issue_date = models.DateField()
    due_date = models.DateField()
    seller = models.CharField(max_length=100)
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    transactions = models.ManyToManyField(Transaction, through='InvoiceTransaction')

    def __str__(self):
        return self.number


class Receipt(models.Model):
    number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE)

    def __str__(self):
        return self.number


class InvoiceTransaction(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('invoice', 'transaction')

    def __str__(self):
        return f'{self.invoice} - {self.transaction}'

