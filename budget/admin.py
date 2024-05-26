from django.contrib import admin
from .models import AccountType, Currency, Category, Account, Goal, Transaction


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    verbose_name = "Тип счета"
    verbose_name_plural = "Типы счетов"


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'exchange_rate')
    search_fields = ('name',)
    list_filter = ('name',)
    verbose_name = "Валюта"
    verbose_name_plural = "Валюты"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type', 'color', 'icon')
    search_fields = ('name', 'user__username')
    list_filter = ('type', 'color', 'icon')
    verbose_name = "Категория"
    verbose_name_plural = "Категории"


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'account_type', 'currency', 'balance', 'initial_balance', 'opening_date', 'closing_date', 'interest_rate', 'credit_limit')
    search_fields = ('name', 'user__username')
    list_filter = ('account_type', 'currency')
    verbose_name = "Счет"
    verbose_name_plural = "Счета"


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'amount')
    search_fields = ('name', 'account__name')
    list_filter = ('account',)
    verbose_name = "Цель"
    verbose_name_plural = "Цели"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'account', 'date', 'amount', 'regular', 'permanent', 'frequency', 'notification_frequency')
    search_fields = ('user__username', 'category__name', 'account__name')
    list_filter = ('category', 'account', 'date', 'regular', 'permanent', 'frequency', 'notification_frequency')
    verbose_name = "Транзакция"
    verbose_name_plural = "Транзакции"


admin.site.site_header = "FinMaster Админка"
admin.site.site_title = "Админ-портал FinMaster"
admin.site.index_title = "Добро пожаловать в админ-портал FinMaster"
