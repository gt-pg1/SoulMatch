from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings


def send_verification_email(request, user, token):
    subject = 'Подтвердите свой аккаунт'
    base_url = f'{request.scheme}://{request.get_host()}'
    confirmation_url = base_url + reverse('email-confirmation', args=[token])
    message = f'Пожалуйста, подтвердите свой аккаунт, перейдя по ссылке: {confirmation_url}'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
