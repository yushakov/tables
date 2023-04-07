from django.contrib import admin
from .models import Construct, Worker, Choice

class ConstructAdmin(admin.ModelAdmin):
    list_display = ["title_text", "goto", "listed_date", "overall_progress", "email"]


admin.site.register(Construct, ConstructAdmin)
admin.site.register(Worker)
admin.site.register(Choice)

