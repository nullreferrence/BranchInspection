# Generated by Django 5.1.5 on 2025-02-26 05:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_workflow', '0007_alter_auditobjection_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='audit_workflow.branch'),
        ),
    ]
