from django.contrib import admin
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.html import format_html
from django.utils import timezone

percent_valid = [MinValueValidator(0), MaxValueValidator(100)] 
phone_valid = [RegexValidator(regex=r'^[+0-9]*$', message='Only numbers and +')]

class Construct(models.Model):
    title_text = models.CharField(max_length=200)
    listed_date = models.DateTimeField('date listed')
    address_text = models.CharField(max_length=500)
    email_text = models.EmailField()
    phone_text = models.CharField(max_length=200, validators=phone_valid)
    owner_name_text = models.CharField(max_length=200)
    overall_progress_percent_num = models.FloatField('progress', default=0.0, validators=percent_valid)
    vat_percent_num = models.FloatField(validators=percent_valid, default='5')
    company_profit_percent_num = models.FloatField(validators=percent_valid, default='15')
    struct_json = models.TextField(default='{}')
    
    def __str__(self):
        return self.title_text

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
    workers = models.ManyToManyField(Worker, default=None)
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
        return self.name_txt + f' ({self.construct})'

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
        super(Choice, self).save(*args, **kwargs)
