from django.contrib import admin
from .models import Construct, Worker, Choice, Invoice, Transaction

class ConstructAdmin(admin.ModelAdmin):
    list_display = ["title_text", "goto", "listed_date", "overall_progress", "email"]

class TransactionAdmin(admin.ModelAdmin):
    list_display = ["get_from_txt", "get_to_txt", "within", "transaction_type", "date", "amount"]

admin.site.register(Construct, ConstructAdmin)
admin.site.register(Worker)
admin.site.register(Choice)
admin.site.register(Invoice)
admin.site.register(Transaction, TransactionAdmin)
