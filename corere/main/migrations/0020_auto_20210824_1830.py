# Generated by Django 3.2.5 on 2021-08-24 18:30

import autoslug.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_auto_20210824_1731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalmanuscript',
            name='contact_email',
            field=models.EmailField(help_text='Email address of the publication contact that will be stored in Dataverse', max_length=254, null=True, verbose_name='Corresponding Author Email Address'),
        ),
        migrations.AlterField(
            model_name='historicalmanuscript',
            name='contact_first_name',
            field=models.CharField(help_text='Given name of the publication contact that will be stored in Dataverse', max_length=150, verbose_name='Corresponding Author Given Name'),
        ),
        migrations.AlterField(
            model_name='historicalmanuscript',
            name='contact_last_name',
            field=models.CharField(help_text='Surname of the publication contact that will be stored in Dataverse', max_length=150, verbose_name='Corresponding Author Surname'),
        ),
        migrations.AlterField(
            model_name='historicalmanuscript',
            name='pub_id',
            field=models.CharField(db_index=True, default='', help_text='The internal ID from the publication', max_length=200, verbose_name='Manuscript #'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='contact_email',
            field=models.EmailField(help_text='Email address of the publication contact that will be stored in Dataverse', max_length=254, null=True, verbose_name='Corresponding Author Email Address'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='contact_first_name',
            field=models.CharField(help_text='Given name of the publication contact that will be stored in Dataverse', max_length=150, verbose_name='Corresponding Author Given Name'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='contact_last_name',
            field=models.CharField(help_text='Surname of the publication contact that will be stored in Dataverse', max_length=150, verbose_name='Corresponding Author Surname'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='pub_id',
            field=models.CharField(db_index=True, default='', help_text='The internal ID from the publication', max_length=200, verbose_name='Manuscript #'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from='get_display_title'),
        ),
    ]
