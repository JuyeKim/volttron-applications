# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-21 20:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vtn', '0044_auto_20171121_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='last_status_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Last Status Time'),
        ),
    ]
