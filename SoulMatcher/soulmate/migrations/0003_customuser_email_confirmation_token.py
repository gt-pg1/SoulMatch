# Generated by Django 4.1.9 on 2023-06-28 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('soulmate', '0002_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='email_confirmation_token',
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
    ]
