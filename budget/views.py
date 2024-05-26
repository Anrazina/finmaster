import calendar
import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import modelformset_factory
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np

import pandas as pd
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

from general_app.forms import CustomUserCreationForm
from .forms import CategoryForm, TransactionForm, AccountForm, GoalForm, CurrencyForm, TransferForm, ForecastForm
from .models import Category, Transaction, Account, Currency
from hwyd.models import Settings
from django.views import View

from functions.voice_input import voice_to_json as vtj
from decimal import Decimal
import json


class LoginRegisterView(View):
    def get(self, request):
        # Если пользователь уже аутентифицирован, перенаправляем на главную страницу
        if request.user.is_authenticated:
            return redirect('budget:index')

        type_form = request.GET.get('type')
        # Отображаем формы для входа и регистрации
        login_form = AuthenticationForm()
        register_form = UserCreationForm()
        return render(request, 'budget/entry.html', {
            'login_form': login_form,
            'register_form': register_form,
            'type_form': type_form,
            'next': request.GET.get('next', '/budget/')
        })

    def post(self, request):
        next_url = request.GET.get('next', '/budget/')
        # Определяем, какую форму отправил пользователь: вход или регистрацию
        login_form, register_form = '', ''
        if 'login' in request.POST:
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = authenticate(
                    username=login_form.cleaned_data['username'],
                    password=login_form.cleaned_data['password']
                )
                if user is not None:
                    login(request, user)
                    return HttpResponseRedirect(next_url)
            # Обработка случая, если форма входа не валидна
            register_form = CustomUserCreationForm()

        elif 'register' in request.POST:
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                login(request, user)
                return HttpResponseRedirect(next_url)
            # Обработка случая, если форма регистрации не валидна
            login_form = AuthenticationForm()

        return render(request, 'budget/entry.html', {
            'login_form': login_form,
            'register_form': register_form
        })


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def transfer_funds(request):
    if request.method == 'POST':
        form = TransferForm(request.user, request.POST)
        if form.is_valid():
            from_account = form.cleaned_data['from_account']
            to_account = form.cleaned_data['to_account']
            amount = form.cleaned_data['amount']

            if from_account.account_type_id == 1:
                from_account.initial_balance -= amount
            else:
                from_account.balance -= amount
            if to_account.account_type_id == 1:
                to_account.initial_balance += amount
            else:
                to_account.balance += amount

            from_account.save()
            to_account.save()

            return redirect('budget:account_list')
    else:
        form = TransferForm(request.user)

    return render(request, 'budget/transfer_funds.html', {'form': form})


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    context_object_name = 'accounts'
    template_name = 'budget/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounts'] = Account.objects.filter(user=self.request.user)
        return context


class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    context_object_name = 'account'
    template_name = 'budget/account_detail.html'


class AccountCreateView(LoginRequiredMixin, CreateView):
    model = Account
    template_name = 'budget/account_form.html'
    success_url = reverse_lazy('budget:account_list')

    def get_form_class(self):
        type_filter = self.request.GET.get('type', 'account')
        if type_filter == 'goal':
            return GoalForm
        return AccountForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        type_filter = self.request.GET.get('type', 'account')
        kwargs['type'] = type_filter
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'budget/account_form.html'

    def get_success_url(self):
        return reverse_lazy('budget:account_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.get_object()
        if account.account_type_id == 1:
            form = GoalForm(instance=account)
        else:
            form = AccountForm(instance=account)
        context['form'] = form
        type_param = self.request.GET.get('type')
        context['type'] = type_param
        return context


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account
    template_name = 'budget/account_confirm_delete.html'
    success_url = reverse_lazy('budget:account_list')


@login_required(login_url='entry')
def transaction_chart(request):
    filter_kwargs = {
        'user': request.user,
        'permanent': False
    }

    # Проверка, есть ли данные POST и они содержат даты
    today = datetime.datetime.today()
    start_date = today.replace(day=1)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    if request.method == 'POST' and 'start-date' in request.POST and 'end-date' in request.POST:
        start_date = request.POST['start-date']
        end_date = request.POST['end-date']

    if start_date:
        filter_kwargs['date__gte'] = start_date
    if end_date:
        filter_kwargs['date__lte'] = end_date

    # Получение фильтрованных данных
    incomes = Transaction.objects.filter(category__type='I', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')
    expenses = Transaction.objects.filter(category__type='E', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')
    transfers = Transaction.objects.filter(category__type='T', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')

    # Форматирование данных
    incomes_data = [{'date': income['date'].strftime('%Y-%m-%d'), 'amount': float(income['total_amount'])} for income in
                    incomes]
    expenses_data = [{'date': expense['date'].strftime('%Y-%m-%d'), 'amount': float(expense['total_amount'])} for
                     expense in expenses]
    transfers_data = [{'date': transfer['date'].strftime('%Y-%m-%d'), 'amount': float(transfer['total_amount'])} for
                      transfer in transfers]

    incomes_json = json.dumps(incomes_data, ensure_ascii=False, cls=DecimalEncoder)
    expenses_json = json.dumps(expenses_data, ensure_ascii=False, cls=DecimalEncoder)
    transfers_json = json.dumps(transfers_data, ensure_ascii=False, cls=DecimalEncoder)

    incomes = Transaction.objects.filter(category__type='I', **filter_kwargs).order_by('-date')
    expenses = Transaction.objects.filter(category__type='E', **filter_kwargs).order_by('-date')
    transfers = Transaction.objects.filter(category__type='T', **filter_kwargs).order_by('-date')

    # Собираем только используемые категории
    if start_date and end_date:
        used_categories = Category.objects.filter(
            transaction__user=request.user,
            transaction__date__range=(start_date, end_date)
        ).distinct()
    else:
        used_categories = Category.objects.filter(
            transaction__user=request.user
        ).distinct()

    categories_data = [
        {
            'name': category.name,
            'total': Transaction.objects.filter(category=category, **filter_kwargs).aggregate(total=Sum('amount'))[
                'total'],
            'color': category.color,
        }
        for category in used_categories
    ]

    return render(request, 'budget/history_finance.html', {
        'incomes_json': incomes_json,
        'expenses_json': expenses_json,
        'transfers_json': transfers_json,
        'incomes': incomes,
        'expenses': expenses,
        'transfers': transfers,
        'categories_json': json.dumps(categories_data, ensure_ascii=False, cls=DecimalEncoder),
    })


@login_required(login_url='entry')
def prediction(request):

    forecast_type = 'days'
    quantity = 10

    if request.POST:
        forecast_type = request.POST.get('forecast_type')
        quantity = int(request.POST.get('quantity'))

    if request.method == 'POST':
        form = ForecastForm(request.POST)
    else:
        form = ForecastForm()

    filter_kwargs = {
        'user': request.user,
        'permanent': False
    }

    # Проверка, есть ли данные POST и они содержат даты
    today = datetime.datetime.today()
    start_date = today.replace(day=1)
    end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    if request.method == 'POST' and 'start-date' in request.POST and 'end-date' in request.POST:
        start_date = request.POST['start-date']
        end_date = request.POST['end-date']

    if start_date:
        filter_kwargs['date__gte'] = start_date
    if end_date:
        filter_kwargs['date__lte'] = end_date

    # Получение фильтрованных данных
    incomes = Transaction.objects.filter(category__type='I', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')
    expenses = Transaction.objects.filter(category__type='E', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')
    transfers = Transaction.objects.filter(category__type='T', **filter_kwargs) \
        .values('date').annotate(total_amount=Sum('amount')).order_by('date')

    # Форматирование данных
    incomes_data = [{'date': income['date'].strftime('%Y-%m-%d'), 'amount': float(income['total_amount'])} for income in
                    incomes]
    expenses_data = [{'date': expense['date'].strftime('%Y-%m-%d'), 'amount': float(expense['total_amount'])} for
                     expense in expenses]
    transfers_data = [{'date': transfer['date'].strftime('%Y-%m-%d'), 'amount': float(transfer['total_amount'])} for
                      transfer in transfers]

    incomes_json = json.dumps(incomes_data, ensure_ascii=False, cls=DecimalEncoder)
    expenses_json = json.dumps(expenses_data, ensure_ascii=False, cls=DecimalEncoder)
    transfers_json = json.dumps(transfers_data, ensure_ascii=False, cls=DecimalEncoder)

    incomes = Transaction.objects.filter(category__type='I', **filter_kwargs).order_by('-date')
    expenses = Transaction.objects.filter(category__type='E', **filter_kwargs).order_by('-date')
    transfers = Transaction.objects.filter(category__type='T', **filter_kwargs).order_by('-date')

    # Собираем только используемые категории
    if start_date and end_date:
        used_categories = Category.objects.filter(
            transaction__user=request.user,
            transaction__date__range=(start_date, end_date)
        ).distinct()
    else:
        used_categories = Category.objects.filter(
            transaction__user=request.user
        ).distinct()

    categories_data = [
        {
            'name': category.name,
            'total': Transaction.objects.filter(category=category, **filter_kwargs).aggregate(total=Sum('amount'))[
                'total'],
            'color': category.color,
        }
        for category in used_categories
    ]

    if forecast_type == 'days':
        forecasted_expenses, forecasted_incomes = get_transactions_for_current_month(request.user, quantity)
    else:
        forecasted_expenses, forecasted_incomes = get_monthly_income_expense(request.user, quantity)

    return render(request, 'budget/prediction.html', {
        'incomes_json': incomes_json,
        'expenses_json': expenses_json,
        'transfers_json': transfers_json,
        'incomes': incomes,
        'expenses': expenses,
        'transfers': transfers,
        'categories_json': json.dumps(categories_data, ensure_ascii=False, cls=DecimalEncoder),
        'forecasted_expenses': json.dumps(forecasted_expenses, ensure_ascii=False, cls=DecimalEncoder),
        'forecasted_incomes': json.dumps(forecasted_incomes, ensure_ascii=False, cls=DecimalEncoder),
        'form': form,
        'quantity': quantity,
        'forecast_type': forecast_type,
    })


@login_required(login_url='entry')
def planning(request):
    today = now().date()

    incomes = Transaction.objects.filter(
        category__type='I',
        user=request.user,
        date__gt=today
    ).order_by('-date')

    expenses = Transaction.objects.filter(
        category__type='E',
        user=request.user,
        date__gt=today
    ).order_by('-date')

    return render(request, 'budget/planning.html', {
        'incomes': incomes,
        'expenses': expenses,
    })


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'budget/category_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = Category.objects.filter(user=self.request.user)
        return context


class CategoryCreate(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'budget/category_form.html'
    success_url = reverse_lazy('budget:category-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = Category.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['type'] = self.request.GET.get('type', 'income')
        return kwargs


class CategoryUpdate(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'budget/category_form.html'
    success_url = reverse_lazy('budget:category-list')


class CategoryDelete(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('budget:category-list')
    template_name = 'budget/category_confirm_delete.html'


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    success_url = reverse_lazy('budget:transaction-list')
    template_name = 'budget/transaction_confirm_delete.html'


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'budget/transaction_form.html'
    success_url = reverse_lazy('budget:transaction-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_trans = self.request.GET.get('type', 'income')
        if type_trans == 'income':
            context['permanent'] = Transaction.objects.filter(user=self.request.user, permanent=True,
                                                              category__type='I').order_by('-date')
        else:
            context['permanent'] = Transaction.objects.filter(user=self.request.user, permanent=True,
                                                              category__type='E').order_by('-date')
        context['type'] = type_trans
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['type'] = self.request.GET.get('type', 'income')

        return kwargs


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = 'transactions'
    template_name = 'budget/transaction_list.html'

    def get_queryset(self):
        today = datetime.datetime.today()
        end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999)

        return Transaction.objects.filter(
            user=self.request.user,
            permanent=False,
            date__lte=end_of_today
        ).order_by('-date')


class PermanentTransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = 'transactions'
    template_name = 'budget/transaction_list.html'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user, permanent=True).order_by('-date')


class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'budget/transaction_form.html'
    success_url = reverse_lazy('budget:transaction-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        account = form.instance.account

        today = now().date()
        if form.instance.date <= today:
            if self.request.GET.get('type', 'income') == 'income':
                account.balance += form.instance.amount
            else:
                account.balance -= form.instance.amount
            account.save()

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_trans = self.request.GET.get('type', 'income')
        if type_trans == 'income':
            context['permanent'] = Transaction.objects.filter(user=self.request.user, permanent=True,
                                                              category__type='I').order_by('-date')
        else:
            context['permanent'] = Transaction.objects.filter(user=self.request.user, permanent=True,
                                                              category__type='E').order_by('-date')
        context['type'] = type_trans
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['type'] = self.request.GET.get('type', 'income')

        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('type') == 'expensee':
            initial.update({
                'amount': 500,
                'category': Category.objects.get(name='Еда'),
                'account': Account.objects.get(name='Стандарт'),
                'date': now().date(),
                'description': 'купила мороженое',
            })
        elif self.request.GET.get('type') == 'incomee':
            initial.update({
                'amount': 3500,
                'category': Category.objects.get(name='Стипендия'),
                'account': Account.objects.get(name='Стандарт'),
                'date': now().date(),
                'description': 'получила стипендию',
            })
        return initial


@login_required(login_url='entry')
def start(request):
    user_profile = Settings.objects.get(user=request.user)
    if request.method == 'POST':
        form = CurrencyForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()

            transactions = Transaction.objects.filter(user=request.user)
            target_currency = Currency.objects.get(name=user_profile.general_currency.name)
            target_exchange_rate = target_currency.exchange_rate

            converted_transactions = []

            for transaction in transactions:
                original_currency = transaction.account.currency
                if original_currency != target_currency:
                    converted_amount = (transaction.amount / original_currency.exchange_rate) * target_exchange_rate
                else:
                    converted_amount = transaction.amount

                converted_transactions.append({
                    'amount': converted_amount,
                    'old_amount': transaction.amount,
                })

            return redirect('budget:index')
    else:
        form = CurrencyForm(instance=user_profile)

    acc = Account.objects.get(name='Стандарт')
    today = now().date() + datetime.timedelta(days=1)
    future_transactions_i = Transaction.objects.filter(date__gt=today, category__type='I', user=request.user)
    future_transactions_e = Transaction.objects.filter(date__gt=today, category__type='E', user=request.user)
    total_future_amount_i = future_transactions_i.aggregate(total=models.Sum('amount'))['total'] or 0
    total_future_amount_e = future_transactions_e.aggregate(total=models.Sum('amount'))['total'] or 0
    total = total_future_amount_i - total_future_amount_e
    if total < 0:
        free = total + acc.balance
    else:
        free = acc.balance
    savings = Account.objects.filter(user=request.user, account_type_id=2).exclude(name='Стандарт').aggregate(
        total=models.Sum('balance'))['total'] or 0
    savings += Account.objects.filter(user=request.user, account_type_id=1).exclude(name='Стандарт').aggregate(
        total=models.Sum('initial_balance'))['total'] or 0
    all_savings = Account.objects.filter(user=request.user, account_type_id=2).aggregate(total=models.Sum('balance'))[
                      'total'] or 0

    acc_amount = acc.balance
    if user_profile.general_currency.name != 'Рубль':
        all_savings = all_savings / user_profile.general_currency.exchange_rate
        total = total / user_profile.general_currency.exchange_rate
        free = free / user_profile.general_currency.exchange_rate
        savings = savings / user_profile.general_currency.exchange_rate
        acc_amount = acc.balance / user_profile.general_currency.exchange_rate

    return render(request, 'budget/budget_home.html',
                  {'form': form, 'account': acc, 'all_savings': round(all_savings, 2), 'general_currency': user_profile.general_currency.name,
                   'planning': round(total, 2), 'free': round(free, 2), 'savings': round(savings, 2), 'acc_amount': round(acc_amount, 2)})


def process_audio(request):
    """
    Создание карточки траты/дохода с помощью голоса
    """

    file = request.FILES.get('audio')
    if not file:
        return HttpResponseBadRequest("No audio file provided")

    res = vtj.wav_to_json(file, request.user)
    res = res.lower()
    print(res)
    if 'перейди' in res:
        if 'доход' in res:
            redirect_url = reverse('budget:transaction-create') + '?type=income'
            return JsonResponse({'redirect_url': redirect_url})
        elif 'трат' in res:
            redirect_url = reverse('budget:transaction-create') + '?type=expense'
            return JsonResponse({'redirect_url': redirect_url})
        elif 'истор' in res:
            return JsonResponse({'redirect_url': reverse('budget:history-finance')})
        elif 'прогноз' in res:
            return JsonResponse({'redirect_url': reverse('budget:prediction')})
        elif 'запланир' in res:
            return JsonResponse({'redirect_url': reverse('budget:planning')})
        elif 'накоплен' in res:
            return JsonResponse({'redirect_url': reverse('budget:account_list')})
        elif 'транзакц' in res or 'счёт' in res:
            return JsonResponse({'redirect_url': reverse('budget:transaction-list')})
        elif 'добав' in res and 'категор' in res:
            return JsonResponse({'redirect_url': reverse('budget:category-add')})
        elif 'категор' in res:
            return JsonResponse({'redirect_url': reverse('budget:category-list')})

    amount, category_name, description, type_trans, date_trans = vtj.wav_to_json(file, request.user, True)

    category_instance = Category.objects.filter(name=category_name.capitalize(), user=request.user).first()

    # Преобразование даты в объект datetime.date
    if isinstance(date_trans, str):
        date_trans = datetime.datetime.strptime(date_trans, "%d.%m.%Y").date()

    # Получение первого аккаунта пользователя (или измените логику по необходимости)
    account_instance = Account.objects.filter(user=request.user).first()

    initial_data = {
        'user': request.user,
        'amount': amount,
        'category': category_instance.id if category_instance else None,
        'description': description,
        'date': date_trans,
        'account': Account.objects.get(pk=account_instance.id) if account_instance else None,
        'regular': False,
        'permanent': False,
        'frequency': None,
        'notification_frequency': None,
        'tags': '',
    }

    form = TransactionForm(initial=initial_data, user=request.user)

    if form.is_valid():

        view = TransactionCreateView()
        view.request = request
        view.object = None
        view.kwargs = {}

        return view.form_valid(form)
    else:
        redirect_url = reverse('budget:transaction-create') + ('?type=incomee' if category_instance.type == 'I' else '?type=expensee')
        return JsonResponse({'redirect_url': redirect_url})


def checks(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        result = body_data.get('result')
        token_acc = "26817.m8ytY4omnqvUob2Sq"
        url = "https://proverkacheka.com/api/v1/check/get"
        data = {"token": token_acc, "qrraw": result}
        r = requests.post(url, data=data)

        if r.status_code != 200 or 'json' not in r.json().get('data', {}):
            return JsonResponse({'error': 'Failed to retrieve data from API'}, status=400)

        products = r.json()['data']['json']['items']
        total_sum = sum(product['sum'] / 100 for product in products)
        description = ', '.join(product['name'] for product in products)

        date_str = r.json()['data']['json']['dateTime']
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        formatted_date = date_obj.strftime('%Y-%m-%d')

        # Создаем экземпляр формы и заполняем ее данными
        form = TransactionForm(initial={
            'category': Category.objects.get(name='Магазин'),
            'account': Account.objects.get(name='Стандарт'),
            'date': formatted_date,
            'amount': total_sum,
            'description': description,
        })

        return render(request, 'budget/transaction_form.html', {'form': form})

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def get_transactions_for_current_month(user, quantity):
    today = datetime.datetime.today()
    start_of_month = today.replace(day=1) - datetime.timedelta(days=360)
    end_of_month = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    transactions = Transaction.objects.filter(date__range=(start_of_month, end_of_month), user=user)

    daily_expenses = []
    daily_incomes = []

    current_date = start_of_month
    while current_date <= end_of_month:
        day_transactions = transactions.filter(date=current_date, user=user)
        total_expenses = day_transactions.filter(category__type='E').aggregate(total=Sum('amount'))['total'] or 0
        total_incomes = day_transactions.filter(category__type='I').aggregate(total=Sum('amount'))['total'] or 0

        daily_expenses.append(float(total_expenses))
        daily_incomes.append(float(total_incomes))

        current_date += datetime.timedelta(days=1)

    periods_to_forecast = quantity
    expenses_model = ExponentialSmoothing(daily_expenses, trend='add', seasonal='add', seasonal_periods=50).fit()
    incomes_model = ExponentialSmoothing(daily_incomes, trend='add', seasonal='add', seasonal_periods=50).fit()

    forecasted_expenses = expenses_model.forecast(periods_to_forecast)
    forecasted_incomes = incomes_model.forecast(periods_to_forecast)

    list_exp = [round(float(e), 2) for e in forecasted_expenses]
    list_inc = [round(float(i), 2) for i in forecasted_incomes]

    return list_exp, list_inc


def get_monthly_income_expense(user, quantity):
    transactions = Transaction.objects.filter(user=user)

    income_per_month = {month: 0 for month in range(1, 13)}
    expense_per_month = {month: 0 for month in range(1, 13)}

    for transaction in transactions:
        month = transaction.date.month
        if transaction.category.type == 'I':
            income_per_month[month] += transaction.amount
        elif transaction.category.type == 'E':
            expense_per_month[month] += abs(transaction.amount)

    income = [float(income_per_month[month]) for month in range(1, 13) if float(income_per_month[month]) != 0.0]
    expense = [float(expense_per_month[month]) for month in range(1, 13) if float(expense_per_month[month]) != 0.0]

    income_series = pd.Series(income)
    expense_series = pd.Series(expense)

    income_model = ExponentialSmoothing(income_series, trend='add', seasonal='add', seasonal_periods=4).fit()
    expense_model = ExponentialSmoothing(expense_series, trend='add', seasonal='add', seasonal_periods=4).fit()

    income_forecast = income_model.forecast(quantity).tolist()
    expense_forecast = expense_model.forecast(quantity).tolist()

    return income_forecast, expense_forecast
