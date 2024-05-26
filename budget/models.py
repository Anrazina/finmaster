from django.db import models
from django.conf import settings
from django.utils import timezone
from taggit.managers import TaggableManager

User = settings.AUTH_USER_MODEL


class AccountType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип счета"
        verbose_name_plural = "Типы счетов"


class Currency(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Курс обмена")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    TYPE_CHOICES = [
        ('I', 'Доход'),
        ('E', 'Расход'),
        ('T', 'Перевод'),
    ]
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    color = models.CharField(max_length=7)
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
    icon = models.CharField(max_length=100, choices=ICON_CHOICES)

    def __str__(self):
        return self.name

    @classmethod
    def get_user_categories(cls, user):
        categories = cls.objects.filter(user=user)
        return ', '.join(category.name for category in categories)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    initial_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opening_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Счёт"
        verbose_name_plural = "Счета"


class Goal(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Цель"
        verbose_name_plural = "Цели"


class Transaction(models.Model):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

    THREE_DAYS_BEFORE = 'three_days_before'
    ONE_DAY_BEFORE = 'one_day_before'
    ON_EVENT_DAY = 'on_event_day'

    FREQUENCY_CHOICES = [
        (DAILY, 'Каждый день'),
        (WEEKLY, 'Каждую неделю'),
        (MONTHLY, 'Каждый месяц'),
        (YEARLY, 'Каждый год'),
    ]

    NOTIFICATION_CHOICES = [
        (THREE_DAYS_BEFORE, 'За три дня'),
        (ONE_DAY_BEFORE, 'За день'),
        (ON_EVENT_DAY, 'В день события'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    regular = models.BooleanField(default=False)
    permanent = models.BooleanField(default=False)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, blank=True)
    notification_frequency = models.CharField(max_length=20, choices=NOTIFICATION_CHOICES, blank=True)

    def __str__(self):
        return f"{self.user} {self.amount} on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
