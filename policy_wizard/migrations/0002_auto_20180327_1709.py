# Generated by Django 2.0 on 2018-03-27 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('policy_wizard', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='policies',
            name='published_by',
            field=models.CharField(max_length=255),
        ),
    ]