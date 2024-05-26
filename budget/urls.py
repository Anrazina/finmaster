from django.urls import path
from .views import start, process_audio, TransactionListView, TransactionCreateView, TransactionUpdateView, \
    TransactionDeleteView, CategoryCreate, CategoryUpdate, CategoryDelete, CategoryList, PermanentTransactionListView, \
    transaction_chart, AccountListView, AccountDetailView, AccountCreateView, AccountUpdateView, AccountDeleteView, \
    planning, transfer_funds, checks, prediction, LoginRegisterView

app_name = 'budget'
urlpatterns = [
    path('', start, name="index"),
    path('process_audio/', process_audio, name="process_audio"),

    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/permanent', PermanentTransactionListView.as_view(), name='permanent-transaction-list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
    path('transaction/<int:pk>/edit/', TransactionUpdateView.as_view(), name='transaction-edit'),
    path('transaction/<int:pk>/delete/', TransactionDeleteView.as_view(), name='transaction-delete'),

    path('category/', CategoryList.as_view(), name='category-list'),
    path('category/add/', CategoryCreate.as_view(), name='category-add'),
    path('category/<int:pk>/', CategoryUpdate.as_view(), name='category-update'),
    path('category/<int:pk>/delete/', CategoryDelete.as_view(), name='category-delete'),

    path('history/', transaction_chart, name='history-finance'),

    path('planning/', planning, name='planning'),

    path('prediction/', prediction, name='prediction'),

    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account_detail'),
    path('accounts/new/', AccountCreateView.as_view(), name='account_new'),
    path('accounts/<int:pk>/edit/', AccountUpdateView.as_view(), name='account_edit'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account_delete'),

    path('transfer-funds/', transfer_funds, name='transfer_funds'),

    path('checks/', checks, name='checks'),

    path('entry/', LoginRegisterView.as_view(), name='entry'),
]
