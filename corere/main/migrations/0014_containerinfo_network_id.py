# Generated by Django 3.1.8 on 2021-04-08 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_containerinfo_network_ip_substring'),
    ]

    operations = [
        migrations.AddField(
            model_name='containerinfo',
            name='network_id',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
