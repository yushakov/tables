from django.contrib import admin
from .models import Construct, Worker, Choice, Invoice, Transaction, InvoiceTransaction

class ConstructAdmin(admin.ModelAdmin):
    list_display = ["title_text", "goto", "listed_date", "overall_progress", "email"]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ["get_from_txt", "get_to_txt", "number_link", "within", "transaction_type", "date", "amount"]

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["seller", "within", "number_link", "invoice_type", "status", "issue_date", "due_date", "amount"]

admin.site.register(Construct, ConstructAdmin)
admin.site.register(Worker)
admin.site.register(Choice)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(InvoiceTransaction)
