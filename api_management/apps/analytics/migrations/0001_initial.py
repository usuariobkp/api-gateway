# Generated by Django 2.0.1 on 2018-01-31 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.CharField(max_length=200, null=True)),
                ('host', models.TextField()),
                ('uri', models.TextField()),
                ('querystring', models.TextField()),
                ('start_time', models.DateTimeField()),
                ('request_time', models.DecimalField(decimal_places=15, max_digits=20)),
            ],
            options={
                'verbose_name': 'query',
                'verbose_name_plural': 'queries',
            },
        ),
    ]