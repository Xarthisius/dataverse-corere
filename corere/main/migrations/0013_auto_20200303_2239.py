# Generated by Django 2.2.10 on 2020-03-03 22:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_auto_20200227_2159'),
    ]

    operations = [
        migrations.RenameField(
            model_name='notes',
            old_name='owner_curation',
            new_name='parent_curation',
        ),
        migrations.RenameField(
            model_name='notes',
            old_name='owner_file',
            new_name='parent_file',
        ),
        migrations.RenameField(
            model_name='notes',
            old_name='owner_submission',
            new_name='parent_submission',
        ),
        migrations.RenameField(
            model_name='notes',
            old_name='owner_verification',
            new_name='parent_verification',
        ),
        migrations.AddField(
            model_name='notes',
            name='manuscript',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.Manuscript'),
        ),
    ]
