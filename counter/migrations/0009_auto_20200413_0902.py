# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-04-13 09:02
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0008_auto_20170122_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='counter',
            name='trigramme',
            field=models.CharField(max_length=3, validators=[django.core.validators.RegexValidator(regex='^\\S{3}$')], verbose_name='trigram'),
        ),
    ]