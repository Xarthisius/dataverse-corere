# Generated by Django 2.2.10 on 2020-05-26 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_auto_20200526_1926'),
    ]

    operations = [
        migrations.AddField(
            model_name='manuscript',
            name='gitlab_submissions_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]