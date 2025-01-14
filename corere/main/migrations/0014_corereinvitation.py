# Generated by Django 3.2.5 on 2021-08-05 17:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0003_auto_20151126_1523'),
        ('main', '0013_auto_20210730_1524'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorereInvitation',
            fields=[
                ('invitation_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='invitations.invitation')),
                ('first_name', models.CharField(max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=150, verbose_name='Last Name')),
            ],
            options={
                'abstract': False,
            },
            bases=('invitations.invitation',),
        ),
    ]
