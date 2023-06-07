from django.forms import ModelForm, ModelMultipleChoiceField
from .models import Transaction, Invoice
from django.utils.translation import gettext_lazy as _


class InvoiceSubmitForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ['construct', 'seller', 'amount','number', 
                  'invoice_type', 'status', 'issue_date', 'due_date', 'photo']
        labels = {
                    'construct': _('Project:'),
                    'seller': _('From:'),
                    'amount': _('Amount:'),
                    'number': _('Number:'),
                    'invoice_type': _('In or Out'),
                    'status': _('Status:'),
                    'issue_date': _('Issue Date:'),
                    'due_date': _('Due Date'),
                    'photo': _('Photo:')
                 }


class TransactionSubmitForm(ModelForm):
    invoice_objects = Invoice.objects.filter(status=Invoice.UNPAID)
    invoices = ModelMultipleChoiceField(queryset=invoice_objects, required=False)
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
        transaction_type = cleaned_data.get('transaction_type')
        photo = cleaned_data.get('photo')
        if construct and invoices and transaction_type:
            for inv in invoices:
                if inv.construct.id != construct.id:
                    self.add_error('invoices', _('Invoices should belong to the same project as the transaction.'))
                if inv.invoice_type != transaction_type:
                    self.add_error('invoices', _('Invoices should be of the same direction (In or Out) as the transaction.'))

    def save(self, commit=True):
        transaction = super(TransactionSubmitForm, self).save(commit=False)
        form_invoices = self.cleaned_data.get('invoices')
        if commit:
            transaction.save()
            for inv in form_invoices:
                transaction.invoice_set.add(inv)
                inv.status = Invoice.PAID
                inv.save()
            inv_tra = transaction.invoicetransaction_set.all()
            for intra in inv_tra:
                intra.construct = transaction.construct
                intra.save()
        return transaction
