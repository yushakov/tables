from django.urls import path
from . import views
from django.shortcuts import redirect


def redirect_to_admin_transactions(request):
    return redirect('admin:list_transaction_changelist')

def redirect_to_admin_invoices(request):
    return redirect('admin:list_invoice_changelist')

app_name = 'list'
urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path('', views.index, name='index'),
    path('history/', views.history, name='history'),
    path('<int:construct_id>/', views.detail, name='detail'),
    path('<int:construct_id>/client/', views.client, name='client'),
    path('<str:slug>', views.client_slug, name='client_slug'),
    path('<int:construct_id>/gantt/', views.gantt, name='gantt'),
    path('<int:construct_id>/flows/', views.flows, name='flows'),
    path('<int:construct_id>/transactions/', views.transactions, name='transactions'),
    path('invoice/', redirect_to_admin_invoices),
    path('invoice/<int:invoice_id>/', views.view_invoice, name='view_invoice'),
    path('invoice/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('invoice/<int:invoice_id>/modify/', views.modify_invoice, name='modify_invoice'),
    path('invoice/submit/', views.submit_invoice, name='submit_invoice'),
    path('transaction/', redirect_to_admin_transactions),
    path('transaction/<int:transaction_id>/', views.view_transaction, name='view_transaction'),
    path('transaction/submit/', views.submit_transaction, name='submit_transaction'),
    path('transaction/bunch/', views.submit_transaction_bunch, name='submit_transaction_bunch'),
    path('<int:construct_id>/clone/', views.clone_construct, name='clone')
]
