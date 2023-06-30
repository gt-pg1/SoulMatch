FROM python:3.10-slim-buster

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY SoulMatcher/participants.jsonl .

COPY . .


RUN python SoulMatcher/manage.py makemigrations soulmate

RUN python SoulMatcher/manage.py migrate

ENV DJANGO_SUPERUSER_USERNAME admin
ENV DJANGO_SUPERUSER_PASSWORD adminpass
ENV DJANGO_SUPERUSER_EMAIL admin@example.com

RUN python SoulMatcher/manage.py createsuperuser --noinput

RUN python SoulMatcher/manage.py import_data

RUN touch /app/data_imported.flag

EXPOSE 8000

CMD ["python", "SoulMatcher/manage.py", "runserver", "0.0.0.0:8000"]

