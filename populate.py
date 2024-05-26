import calendar
from datetime import datetime, timedelta

from faker import Faker
import random
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_site.settings')
django.setup()

from budget.models import AccountType, Currency, Category, Account, Goal, Transaction
from django.contrib.auth import get_user_model

fake = Faker('ru_RU')
User = get_user_model()

user = User.objects.get(id=259)
categories = Category.objects.filter(user=user, type='I')
account = Account.objects.get(name='Стандарт')

for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
    today = datetime.today() - timedelta(days=30 * i)
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    for _ in range(5):
        user = user
        category = random.choice(categories)
        account = account
        date = fake.date_between(start_date=start_of_month, end_date=end_of_month)
        amount = round(random.uniform(100, 10000), 2)
        description = category.name
        regular = False
        permanent = False
        frequency = random.choice([choice[0] for choice in Transaction.FREQUENCY_CHOICES])
        notification_frequency = random.choice([choice[0] for choice in Transaction.NOTIFICATION_CHOICES])

        # Создание и сохранение транзакции
        Transaction.objects.create(
            user=user,
            category=category,
            account=account,
            date=date,
            amount=amount,
            description=description,
            regular=regular,
            permanent=permanent,
            frequency=frequency,
            notification_frequency=notification_frequency
        )

    print("Транзакции успешно сгенерированы и сохранены в базу данных.")
