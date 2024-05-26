from django import forms
from django.utils.encoding import force_str
from taggit.forms import TagWidget
from .models import Transaction, Category, Account
from hwyd.models import Settings

from django import forms
from .models import Account
from django.utils.html import format_html


class ForecastForm(forms.Form):
    FORECAST_CHOICES = [
        ('days', 'Дни'),
        ('months', 'Месяцы'),
    ]

    forecast_type = forms.ChoiceField(
        choices=FORECAST_CHOICES,
        label='Тип прогнозирования',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    quantity = forms.IntegerField(
        min_value=1,
        label='Количество',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'value': 10})
    )


class IconSelectWidget(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value:
            option['attrs']['data-icon'] = f'fa fa-{value}'
        return option


class TransferForm(forms.Form):
    from_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label="Со счёта",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    to_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        label="На",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Количество",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_account'].queryset = Account.objects.filter(user=user)
        self.fields['to_account'].queryset = Account.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get("from_account")
        to_account = cleaned_data.get("to_account")
        amount = cleaned_data.get("amount")

        if from_account == to_account:
            raise forms.ValidationError("Cannot transfer to the same account.")

        if from_account.balance < amount:
            raise forms.ValidationError("Insufficient balance in the from account.")

        return cleaned_data


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'account', 'date', 'amount', 'description', 'tags', 'frequency', 'notification_frequency', 'permanent']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '1'}),
            'tags': TagWidget(attrs={'class': 'form-control'}),
            'regular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permanent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'notification_frequency': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'category': 'Категория',
            'account': 'Счет',
            'date': 'Дата',
            'amount': 'Сумма',
            'description': 'Описание',
            'tags': 'Теги',
            'regular': 'Регулярная',
            'permanent': 'Постоянная',
            'frequency': 'Частота',
            'notification_frequency': 'Уведомления',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        type_filter = kwargs.pop('type', 'income')
        super(TransactionForm, self).__init__(*args, **kwargs)
        if user is not None:
            categories = Category.objects.filter(user=user)
            if type_filter == 'income':
                categories = categories.filter(type='I')
            elif type_filter == 'expense':
                categories = categories.filter(type='E')
            self.fields['category'].queryset = categories
            self.fields['account'].queryset = Account.objects.filter(user=user, account_type_id=2)


class CategoryForm(forms.ModelForm):
    ICON_CHOICES = [
        ('heartbeat', 'Уход'),  # Сердцебиение
        ('money-bill-wave', 'Зарплата'),  # Банкнота с волной
        ('graduation-cap', 'Стипендия'),  # Шапка выпускника
        ('utensils', 'Еда'),  # Столовые приборы
        ('tint', 'Вода'),  # Капля
        ('gift', 'Подарок'),  # Подарок
        ('user-alt', 'Пенсия'),  # Пользователь (альтернативный)
        ('home', 'Аренда'),  # Дом
        ('hand-holding-usd', 'Кэшбек'),  # Рука, держащая доллар
        ('bus', 'Транспорт'),  # Автобус
        ('building', 'Жилье'),  # Здание
        ('phone', 'Связь'),  # Телефон
        ('tshirt', 'Одежда и обувь'),  # Футболка
        ('heartbeat', 'Здоровье'),  # Сердцебиение
        ('film', 'Развлечение и досуг'),  # Пленка
        ('book', 'Образование'),  # Книга
        ('paw', 'Домашние животные'),  # Лапа
        ('dumbbell', 'Спорт'),  # Гантель
        ('shopping-cart', 'Магазин'),  # Корзина покупок
        ('money-bill', 'Банкнота'),
        ('wallet', 'Кошелек'),
        ('credit-card', 'Кредитная карта'),
        ('piggy-bank', 'Копилка'),
        ('coins', 'Монеты'),
        ('chart-line', 'Линейный график'),
        ('chart-bar', 'Гистограмма'),
        ('chart-pie', 'Круговая диаграмма'),
        ('balance-scale', 'Весы'),
        ('file-invoice-dollar', 'Счет-фактура в долларах'),
        ('receipt', 'Квитанция'),
        ('calculator', 'Калькулятор'),
        ('calendar-alt', 'Календарь'),
        ('hand-holding-usd', 'Рука, держащая доллар'),
        ('donate', 'Пожертвование'),
        ('file-alt', 'Документ'),
        ('shopping-cart', 'Корзина покупок'),
        ('exchange-alt', 'Обмен'),
        ('money-check-alt', 'Чек'),
        ('business-time', 'Рабочее время'),
        ('sack-dollar', 'Мешок с долларами'),
        ('cash-register', 'Кассовый аппарат'),
        ('handshake', 'Рукопожатие'),
        ('chart-area', 'Площадная диаграмма'),
        ('briefcase', 'Портфель'),
        ('clipboard', 'Блокнот'),
        ('file-contract', 'Договор'),
        ('cogs', 'Шестеренки'),
        ('chart-line', 'Линейный график'),
        ('comments-dollar', 'Комментарии в долларах'),
        ('gift', 'Подарок'),
        ('percent', 'Процент'),
        ('arrow-down', 'Стрелка вниз'),
        ('arrow-up', 'Стрелка вверх'),
        ('chart-pie', 'Круговая диаграмма'),
        ('arrow-left', 'Стрелка влево'),
        ('arrow-right', 'Стрелка вправо'),
        ('clipboard-list', 'Список дел'),
        ('tasks', 'Задачи'),
        ('lock', 'Замок'),
        ('unlock', 'Разблокировать'),
        ('users', 'Пользователи'),
        ('user', 'Пользователь'),
        ('user-tie', 'Пользователь с галстуком'),
    ]

    class Meta:
        model = Category
        fields = ['name', 'type', 'color', 'icon']
        labels = {
            'user': 'Пользователь',
            'name': 'Название',
            'type': 'Тип',
            'color': 'Цвет',
            'icon': 'Иконка',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(choices=Category.TYPE_CHOICES, attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'icon': IconSelectWidget(attrs={'class': 'form-control icon-select'}),
        }

    def __init__(self, *args, **kwargs):
        type_filter = kwargs.pop('type', 'income')
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 'I' if type_filter == 'income' else 'E'
        self.fields['icon'].choices = self.ICON_CHOICES


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_type', 'currency', 'name', 'balance', 'initial_balance', 'opening_date',
                  'closing_date', 'interest_rate', 'credit_limit']
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'opening_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'closing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'account_type': 'Тип счета',
            'currency': 'Валюта',
            'name': 'Название',
            'balance': 'Баланс',
            'initial_balance': 'Начальный баланс',
            'opening_date': 'Дата открытия',
            'closing_date': 'Дата закрытия',
            'interest_rate': 'Процентная ставка',
            'credit_limit': 'Кредитный лимит',
        }

    def __init__(self, *args, **kwargs):
        type_filter = kwargs.pop('type', 'account')
        super(AccountForm, self).__init__(*args, **kwargs)
        self.fields['account_type'].initial = 2


class GoalForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_type', 'currency', 'name', 'balance', 'closing_date']
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'closing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
        labels = {
            'account_type': 'Тип счета',
            'currency': 'Валюта',
            'name': 'Название',
            'balance': 'Стоимость',
            'closing_date': 'Дедлайн',
        }

    def __init__(self, *args, **kwargs):
        type_filter = kwargs.pop('type', 'goal')
        super(GoalForm, self).__init__(*args, **kwargs)
        self.fields['account_type'].initial = 1


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['general_currency']
        widgets = {
            'general_currency': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'general_currency': 'Стандартная валюта',
        }
