# Generated by Django 3.2.2 on 2021-06-16 19:22

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_auto_20210616_1912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluser',
            name='last_oauthproxy_forced_signin',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0)),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_oauthproxy_forced_signin',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0)),
        ),
    ]
