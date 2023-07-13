from django.contrib import admin
from .models import Construct, Worker, Choice, Invoice, Transaction, InvoiceTransaction

'''
Customization tricks: https://realpython.com/customize-django-admin-python 
'''

class ConstructAdmin(admin.ModelAdmin):
    list_display = ["title_text", "goto", "listed_date", "overall_progress", "email"]
    search_fields = ["title_text"]
    fields = ["title_text",
              "address_text",
              "email_text",
              "phone_text",
              "owner_name_text",
              "assigned_to",
              "vat_percent_num",
              "company_profit_percent_num",
              "owner_profit_coeff"]

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["title_text"].label = "Name"
        form.base_fields["address_text"].label = "Address"
        form.base_fields["email_text"].label = "Email"
        form.base_fields["phone_text"].label = "Phone"
        form.base_fields["owner_name_text"].label = "Owner"
        form.base_fields["vat_percent_num"].label = "VAT, %"
        form.base_fields["company_profit_percent_num"].label = "Company profit, %"
        form.base_fields["owner_profit_coeff"].label = "Owner profit coefficient"
        return form

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["get_name", "get_progress"]
    list_filter  = ["construct"]
    search_fields = ["name_txt__contains"]
    fields = ["construct", "workers", "name_txt",
              "quantity_num", "units_of_measure_text", "price_num",
              "progress_percent_num",
              "plan_start_date", "plan_days_num",
              "actual_start_date", "actual_end_date",
              "constructive_notes", "client_notes"]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ["get_from_txt", "get_to_txt", "number_link", "within", "get_type", "date", "amount"]
    list_filter = ["construct"]

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["seller", "within", "number_link", "invoice_type", "status", "issue_date", "due_date", "amount"]
    list_filter = ["construct"]

admin.site.register(Construct, ConstructAdmin)
admin.site.register(Worker)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(InvoiceTransaction)
