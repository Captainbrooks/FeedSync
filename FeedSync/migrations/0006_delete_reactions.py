# Generated by Django 5.0.6 on 2024-07-29 02:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('FeedSync', '0005_reactions'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Reactions',
        ),
    ]