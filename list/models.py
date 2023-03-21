from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

percent_valid = [MinValueValidator(0), MaxValueValidator(100)] 

class Construct(models.Model):
    title_text = models.CharField(max_length=200)
    listed_date = models.DateTimeField('date listed')
    address_text = models.CharField(max_length=500)
    email_text = models.CharField(max_length=200)
    phone_text = models.CharField(max_length=200)
    owner_name_text = models.CharField(max_length=200)
    overall_progress_percent_num = models.FloatField('progress', default=0.0, validators=percent_valid)
    
    def __str__(self):
        return self.title_text


class Choice(models.Model):
    construct = models.ForeignKey(Construct, on_delete=models.CASCADE)
    name_txt = models.CharField(max_length=200)
    notes_txt = models.CharField(max_length=5000, default='-')
    quantity_num = models.FloatField(default='1')
    units_of_measure_text = models.CharField(max_length=100, default='-')
    price_num = models.FloatField()
    vat_percent_num = models.FloatField(validators=percent_valid, default='5')
    company_profit_percent_num = models.FloatField(validators=percent_valid, default='15')
    assigned_to_txt = models.CharField(max_length=200)
    progress_percent_num = models.FloatField(validators=percent_valid, default='0')
    plan_start_date = models.DateField()
    plan_days_num = models.FloatField()
    actual_start_date = models.DateField()
    actual_end_date = models.DateField()

    def __str__(self):
        return self.name_txt + f' ({self.construct})'
