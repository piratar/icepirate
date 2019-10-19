# Generated by Django 2.0.13 on 2019-10-19 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0002_membergroup_admins'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membergroup',
            name='combination_method',
            field=models.CharField(choices=[('union', 'Union'), ('intersection', 'Intersection')], default='union', max_length=30, verbose_name='Combination method'),
        ),
    ]