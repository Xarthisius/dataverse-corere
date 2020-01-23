# Generated by Django 2.2 on 2020-01-23 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='author_submissions',
            field=models.ManyToManyField(related_name='authors', to='main.Submission'),
        ),
        migrations.AlterField(
            model_name='user',
            name='curator_curations',
            field=models.ManyToManyField(related_name='curators', to='main.Curation'),
        ),
        migrations.AlterField(
            model_name='user',
            name='editor_manuscripts',
            field=models.ManyToManyField(related_name='editors', to='main.Manuscript'),
        ),
        migrations.AlterField(
            model_name='user',
            name='verifier_verifications',
            field=models.ManyToManyField(related_name='verifiers', to='main.Verification'),
        ),
    ]
