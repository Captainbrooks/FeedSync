# Generated by Django 5.0.6 on 2024-08-01 05:11

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('FeedSync', '0010_friendship'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friendship',
            unique_together={('receiver', 'sender'), ('sender', 'receiver')},
        ),
    ]