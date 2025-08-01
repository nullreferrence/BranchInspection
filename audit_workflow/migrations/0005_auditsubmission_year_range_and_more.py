# Generated by Django 5.1.5 on 2025-02-18 07:33

import django.core.validators
import django_ckeditor_5.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_workflow', '0004_rename_case_comment_submission_comment_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditsubmission',
            name='year_range',
            field=models.CharField(default=234, max_length=9, validators=[django.core.validators.RegexValidator('^\\d{4}-\\d{4}$', 'Invalid year range format.')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='auditobjection',
            name='description',
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name='Description'),
        ),
    ]
