import json
import uuid
import transliterate
import re
from tqdm import tqdm

from django.db import transaction

from soulmate.models import CustomUser, Priority


def import_data_from_json(file_name):
    users_to_create = []
    priorities_to_create = []

    # Открываем файл и считаем количество строк
    with open(file_name, 'r', encoding='utf-8') as file:
        total_lines = sum(1 for _ in file)

    # Открываем файл снова и создаем прогресс-бар для чтения файла
    with open(file_name, 'r', encoding='utf-8') as file:
        for index, line in enumerate(tqdm(file, total=total_lines, desc="Reading file")):
            record = json.loads(line)
            name = record.get('name')
            precedents = record.get('precedents', {})

            surname, firstname = name.split(' ')
            latin_surname = re.sub(r'[^a-zA-Z0-9.@]', '', transliterate.translit(surname, reversed=True).lower())
            latin_firstname = re.sub(r'[^a-zA-Z0-9.@]', '', transliterate.translit(firstname, reversed=True).lower())
            email = f"{latin_surname}.{latin_firstname}@test.com"
            username = f"{latin_surname}{latin_firstname}{100000 + index}"

            # Создание пользователя
            user = CustomUser(
                username=username,
                first_name=firstname,
                last_name=surname,
                email=email,
                password="aB998877",
                email_confirmed=True,
                email_confirmation_token=str(uuid.uuid4())
            )
            users_to_create.append(user)

    # Использование транзакции для ускорения вставки данных
    with transaction.atomic():
        # Добавляем пользователей в БД и отображаем прогресс
        user_progress_bar = tqdm(total=len(users_to_create), desc="Writing users to DB")
        created_users = CustomUser.objects.bulk_create(users_to_create)
        user_progress_bar.update(len(users_to_create))
        user_progress_bar.close()

        # Добавляем приоритеты в БД и отображаем прогресс
        for user in created_users:
            for aspect, details in precedents.items():
                attitude = details.get('attitude')
                weight = details.get('importance')

                priority = Priority(
                    user=user,
                    aspect=aspect,
                    attitude=attitude,
                    weight=weight
                )
                priorities_to_create.append(priority)

        priority_progress_bar = tqdm(total=len(priorities_to_create), desc="Writing priorities to DB")
        Priority.objects.bulk_create(priorities_to_create)
        priority_progress_bar.update(len(priorities_to_create))
        priority_progress_bar.close()


import_data_from_json("participants.jsonl")
