# Generated by Django 2.0.1 on 2019-01-16 19:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_registry', '0015_kongapihistorichits'),
    ]

    operations = [
        migrations.RenameField(
            model_name='kongapihistorichits',
            old_name='kong_id',
            new_name='kong_api',
        ),
    ]