# Generated by Django 2.2 on 2020-02-03 19:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_user_invite_key'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_author',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_curator',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_editor',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_verifier',
        ),
        migrations.AddField(
            model_name='user',
            name='invited_by',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
