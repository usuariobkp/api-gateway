# Generated by Django 2.0.1 on 2018-04-12 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_registry', '0014_auto_20180411_1510'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applicant', models.CharField(max_length=100)),
                ('contact_email', models.EmailField(max_length=254)),
                ('consumer_application', models.CharField(max_length=200)),
                ('requests_per_day', models.IntegerField()),
            ],
        ),
    ]