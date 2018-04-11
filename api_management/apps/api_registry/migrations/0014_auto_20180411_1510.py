# Generated by Django 2.0.1 on 2018-04-11 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_registry', '0013_apidata_httplog2_ga_exclude_regex'),
    ]

    operations = [
        migrations.AddField(
            model_name='apidata',
            name='jwt_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='apidata',
            name='jwt_kong_id',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
