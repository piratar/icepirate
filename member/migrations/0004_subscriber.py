# Generated by Django 2.2.13 on 2020-09-30 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0003_auto_20191019_1416'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(max_length=75, unique=True)),
                ('email_verified', models.BooleanField(default=False)),
                ('email_verified_timing', models.DateTimeField(null=True)),
                ('temporary_web_id', models.CharField(max_length=40, null=True, unique=True)),
                ('temporary_web_id_timing', models.DateTimeField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
