from django import template

register = template.Library()


@register.filter
def translate_frequency(value):
    translations = {
        'daily': 'Каждый день',
        'weekly': 'Каждую неделю',
        'monthly': 'Каждый месяц',
        'yearly': 'Каждый год',
        'three_days_before': 'За три дня',
        'one_day_before': 'За день',
        'on_event_day': 'В день события'
    }
    return translations.get(value, value)
