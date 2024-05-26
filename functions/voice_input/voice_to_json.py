import os
import re
from datetime import datetime

import g4f
import json
import tempfile
from pathlib import Path
import speech_recognition as sr
from budget.models import Category

BASE_DIR = Path(__file__).resolve().parent.parent
HOSTING = str(BASE_DIR).find('jim') == -1
DIRECTION = '/home/a0853298/tmp/' if HOSTING else 'C:/Users/jim/Desktop/my_site/test'


def recognize_phrase(phrase_wav_path: str) -> str:
    """
    Распознавание голоса в wav с помощью Google
    """

    recognizer = sr.Recognizer()
    with sr.AudioFile(phrase_wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="ru-RU")
        except sr.UnknownValueError:
            text = 'exception'
        except sr.RequestError:
            text = 'exception'

    return text


def chat_gpt(text, user):
    """
    Запрос в Chat GPT для получение JSON из текста
    """

    current_year = datetime.now().year
    user_categories = Category.get_user_categories(user)

    content = f"{text}. Пиши названия ключей на русском языке. Выбери из этого текста сумма, категория, описание (в описании выдели остальную информацию), тип транзакции (расход или доход) и дату и помести это в JSON. Сумма должна быть цифрой, а категория строкой. Категория должна быть похожа, как в списке {user_categories}. Описание должно быть текстом. Тип транзакции 'I' если доход 'E' если расход. Дата в формате dd.mm.yyyy, если не назван год, то ставь текущий. Запятые в json не добавляй."

    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_35_turbo_0613,
            messages=[{"role": "user", "content": content}]
        )

        response_text = response.lower()
        json_data_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if not json_data_match:
            raise ValueError("JSON not found in response")

        json_data = json_data_match.group(0)
        result = json.loads(json_data)

        amount = None
        category = None
        description = None
        type_trans = None
        date_trans = None

        for key, value in result.items():
            lower_key = key.lower()
            if 'сум' in lower_key:
                amount = value
            elif 'кате' in lower_key:
                category = value
            elif 'опис' in lower_key:
                description = value
            elif 'тип' in lower_key:
                type_trans = value
            elif 'дат' in lower_key:
                if '.' in value and len(value.split('.')[-1]) == 2:
                    value = value + f'.{current_year}'
                date_trans = value

        return amount, category, description, type_trans, date_trans

    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None, None


def wav_to_json(file, user, type_gpt=False):
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False, dir=DIRECTION) as temp_file:

        for chunk in file.chunks():
            temp_file.write(chunk)

        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.seek(0)

        res = recognize_phrase(temp_file.name)

    temp_file.close()
    os.remove(temp_file.name)

    if type_gpt:
        # return chat_gpt(res, user)
        return 500, 'еда', 'купил мороженое', 'e', '20.05.2024'

    if res == 'exception':
        return res

    return res
