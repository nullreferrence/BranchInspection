# Generated by Django 5.1.5 on 2025-03-06 09:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_workflow', '0010_alter_upload_document'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='case_id',
        ),
        migrations.RemoveField(
            model_name='personel_decision',
            name='case_no',
        ),
        migrations.AddField(
            model_name='person',
            name='audit_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='audit_workflow.auditsubmission'),
        ),
        migrations.AddField(
            model_name='person',
            name='items',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='audit_workflow.items'),
        ),
        migrations.AddField(
            model_name='personel_decision',
            name='audit_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='audit_workflow.auditsubmission'),
        ),
    ]
