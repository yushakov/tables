from django.urls import path

from . import views

app_name = 'list'
urlpatterns = [
    #path('', views.IndexView.as_view(), name='index'),
    path('', views.index, name='index'),
    path('<int:construct_id>/', views.detail, name='detail'),
    path('<int:construct_id>/gantt/', views.gantt, name='gantt'),
    path('invoice/<int:invoice_id>/', views.view_invoice, name='view_invoice'),
    path('transaction/<int:transaction_id>/', views.view_transaction, name='view_transaction'),
    path('transaction/submit/', views.submit_transaction, name='submit_transaction')
]
