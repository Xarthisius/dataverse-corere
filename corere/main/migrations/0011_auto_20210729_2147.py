# Generated by Django 3.2.5 on 2021-07-29 21:47

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20210709_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalmanuscript',
            name='_status',
            field=django_fsm.FSMField(choices=[('new', 'New'), ('awaiting_init', 'Awaiting Initial Submission'), ('awaiting_resub', 'Awaiting Resubmission'), ('reviewing', 'Editor Reviewing'), ('processing', 'Processing Submission'), ('completed', 'Completed')], default='new', help_text='The overall status of the manuscript in the review process', max_length=15, verbose_name='Manuscript Status'),
        ),
        migrations.AlterField(
            model_name='historicalsubmission',
            name='_status',
            field=django_fsm.FSMField(choices=[('new', 'New'), ('in_progress_edition', 'In Progress Edition'), ('rejected_editor', 'Rejected Editor'), ('in_progress_curation', 'In Progress Curation'), ('in_progress_verification', 'In Progress Verification'), ('reviewed_awaiting_report', 'Reviewed Awaiting Report'), ('reviewed_awaiting_approve', 'Reviewed Report Awaiting Approval'), ('returned', 'Returned')], default='new', help_text='The status of the submission in the review process', max_length=25, verbose_name='Submission review status'),
        ),
        migrations.AlterField(
            model_name='manuscript',
            name='_status',
            field=django_fsm.FSMField(choices=[('new', 'New'), ('awaiting_init', 'Awaiting Initial Submission'), ('awaiting_resub', 'Awaiting Resubmission'), ('reviewing', 'Editor Reviewing'), ('processing', 'Processing Submission'), ('completed', 'Completed')], default='new', help_text='The overall status of the manuscript in the review process', max_length=15, verbose_name='Manuscript Status'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='_status',
            field=django_fsm.FSMField(choices=[('new', 'New'), ('in_progress_edition', 'In Progress Edition'), ('rejected_editor', 'Rejected Editor'), ('in_progress_curation', 'In Progress Curation'), ('in_progress_verification', 'In Progress Verification'), ('reviewed_awaiting_report', 'Reviewed Awaiting Report'), ('reviewed_awaiting_approve', 'Reviewed Report Awaiting Approval'), ('returned', 'Returned')], default='new', help_text='The status of the submission in the review process', max_length=25, verbose_name='Submission review status'),
        ),
    ]
