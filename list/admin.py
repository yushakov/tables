from django.contrib import admin
from .models import Construct, Worker, Choice, Invoice, Transaction

class ConstructAdmin(admin.ModelAdmin):
    list_display = ["title_text", "goto", "listed_date", "overall_progress", "email"]


admin.site.register(Construct, ConstructAdmin)
admin.site.register(Worker)
admin.site.register(Choice)
admin.site.register(Invoice)
admin.site.register(Transaction)
