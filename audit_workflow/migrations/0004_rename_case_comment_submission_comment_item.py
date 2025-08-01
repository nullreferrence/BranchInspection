# Generated by Django 5.1.5 on 2025-02-17 12:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_workflow', '0003_remove_comment_case_no_comment_case_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='case',
            new_name='submission',
        ),
        migrations.AddField(
            model_name='comment',
            name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='audit_workflow.items'),
        ),
    ]
