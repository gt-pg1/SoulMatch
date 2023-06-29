from tqdm import tqdm
import json
import re
import uuid
import transliterate
from django.db import transaction
from soulmate.models import CustomUser, Aspect, Attitude, Weight, Priority


def import_data_from_json(file_name):
    users_to_create = []
    priority_relations = []

    with open(file_name, 'r', encoding='utf-8') as file:
        total_lines = sum(1 for _ in file)

    aspects_cache = {aspect.aspect: aspect for aspect in Aspect.objects.all()}
    attitudes_cache = {attitude.attitude: attitude for attitude in Attitude.objects.all()}
    weights_cache = {weight.weight: weight for weight in Weight.objects.all()}

    with open(file_name, 'r', encoding='utf-8') as file:
        for index, line in enumerate(tqdm(file, total=total_lines, desc="Reading file", leave=False)):
            record = json.loads(line)
            name = record.get('name')
            aspects = record.get('precedents', {})

            surname, firstname = name.split(' ')
            latin_surname = re.sub(r'[^a-zA-Z0-9.@]', '', transliterate.translit(surname, reversed=True).lower())
            latin_firstname = re.sub(r'[^a-zA-Z0-9.@]', '', transliterate.translit(firstname, reversed=True).lower())
            username = f"{latin_surname}{latin_firstname}{100000 + index}"
            email = f"{username}@test.com"

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

            for aspect_name, details in aspects.items():
                attitude_name = details.get('attitude')
                weight_value = details.get('importance')

                aspect = aspects_cache.get(aspect_name)
                if aspect is None:
                    aspect = Aspect.objects.create(aspect=aspect_name)
                    aspects_cache[aspect_name] = aspect

                attitude = attitudes_cache.get(attitude_name)
                if attitude is None:
                    attitude = Attitude.objects.create(attitude=attitude_name)
                    attitudes_cache[attitude_name] = attitude

                weight = weights_cache.get(weight_value)
                if weight is None:
                    weight = Weight.objects.create(weight=weight_value)
                    weights_cache[weight_value] = weight

                priority_relations.append((user, aspect, attitude, weight))

    with transaction.atomic():
        tqdm.write("Writing users to DB...")
        CustomUser.objects.bulk_create(users_to_create)

        tqdm.write("Writing priorities to DB...")
        progress_bar = tqdm(total=len(priority_relations), desc="Writing priorities to DB", leave=False)
        for user, aspect, attitude, weight in priority_relations:
            priority = Priority.objects.create(aspect=aspect, attitude=attitude, weight=weight)
            priority.users.add(user)
            progress_bar.update(1)
        progress_bar.close()


import_data_from_json("participants.jsonl")
