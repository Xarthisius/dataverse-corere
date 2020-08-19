# Generated by Django 2.2.14 on 2020-08-07 17:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_squashed_0027_auto_20200710_1637'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='manuscript',
            options={'permissions': [('add_authors_on_manuscript', 'Can manage authors on manuscript'), ('remove_authors_on_manuscript', 'Can manage authors on manuscript'), ('manage_editors_on_manuscript', 'Can manage editors on manuscript'), ('manage_curators_on_manuscript', 'Can manage curators on manuscript'), ('manage_verifiers_on_manuscript', 'Can manage verifiers on manuscript'), ('add_submission_to_manuscript', 'Can add submission to manuscript'), ('curate_manuscript', 'Can curate manuscript/submission'), ('verify_manuscript', 'Can verify manuscript/submission')]},
        ),
    ]