from django.forms import ModelForm, ModelMultipleChoiceField
from .models import Transaction, Invoice
from django.utils.translation import gettext_lazy as _

class TransactionSubmitForm(ModelForm):
    invoices = ModelMultipleChoiceField(queryset=Invoice.objects.all())
    class Meta:
        model = Transaction
        fields = ['from_txt', 'to_txt', 'amount', 'transaction_type',
                  'construct', 'date', 'receipt_number', 'invoices',
                  'details_txt', 'photo']
        labels = {
                  'from_txt': _('From:'),
                  'to_txt': _('To:'),
                  'amount': _('Amount:'),
                  'transaction_type': _('In or Out of project:'),
                  'construct': _('Project:'),
                  'date': _('Transaction date:'),
                  'receipt_number': _('Receipt number:'),
                  'invoices': _('To pay for:'),
                  'details_txt': _('Details or Notes:'),
                  'photo': _('Photo')
                  }

    def clean(self):
        cleaned_data = super().clean()
        construct = cleaned_data.get('construct')
        invoices  = cleaned_data.get('invoices')
        if construct and invoices:
            for inv in invoices:
                if inv.construct.id != construct.id:
                    self.add_error('invoices', _('Invoices should belong to the same project as the transaction.'))
