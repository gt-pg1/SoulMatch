from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Count

from ...models import Priority


class Command(BaseCommand):
    help = 'Отправка электронной почты пользователям с лучшими предпочтениями'

    def get_top_three_priorities(self, user):
        # Получить список идентификаторов аспектов, которые уже заполнены пользователем
        user_priorities_ids = Priority.objects.filter(users__in=[user]).values_list('aspect__id', flat=True)

        # Получить топ 3 наиболее популярных аспектов, исключая те, которые уже заполнены пользователем
        aspects_with_count = Priority.objects.exclude(
            aspect__id__in=user_priorities_ids
        ).values(
            'aspect__aspect'
        ).annotate(
            total=Count('aspect__aspect')
        ).order_by('-total')[:3]
        return aspects_with_count

    def handle(self, *args, **kwargs):
        users = get_user_model().objects.all()
        for user in users:
            top_priorities = self.get_top_three_priorities(user)
            cache_key = f'user_{user.id}_top_priorities'
            print(f"Setting cache: Key - {cache_key}, Value - {top_priorities}")
            cache.set(cache_key, top_priorities, 86400)
            print(f"Cache set: Key - {cache_key}, Value - {cache.get(cache_key)}")
            top_priorities_str = ', '.join([f"{item['aspect__aspect']} ({item['total']})" for item in top_priorities])

            send_mail(
                'Лучшие приоритеты для вас',
                top_priorities_str,
                'from@example.com',
                [user.email],
                fail_silently=False,
            )
