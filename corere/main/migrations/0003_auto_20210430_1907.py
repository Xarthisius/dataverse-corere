# Generated by Django 3.1.8 on 2021-04-30 19:07

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20210428_1903'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='last_oauthproxy_forced_signin',
            field=models.DateTimeField(default=datetime.date(1900, 1, 1)),
        ),
        migrations.AddField(
            model_name='user',
            name='last_oauthproxy_forced_signin',
            field=models.DateTimeField(default=datetime.date(1900, 1, 1)),
        ),
    ]
