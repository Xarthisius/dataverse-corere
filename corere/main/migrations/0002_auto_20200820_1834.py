# Generated by Django 2.2.15 on 2020-08-20 18:34

from django.db import migrations, models
from datetime import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gitlabfile',
            name='gitlab_date',
            field=models.DateTimeField(default=datetime.now()),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name='gitlabfile',
            index=models.Index(fields=['gitlab_path', 'parent_submission'], name='main_gitlab_gitlab__c5f97e_idx'),
        ),
    ]
