# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-14 20:29
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vtn', '0025_auto_20171114_1925'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteevent',
            name='previous_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='vtn.SiteEvent'),
        ),
        migrations.AlterField(
            model_name='drevent',
            name='last_status_time',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 11, 14, 20, 29, 13, 124308), null=True, verbose_name='Last Status Time'),
        ),
        migrations.AlterField(
            model_name='siteevent',
            name='last_opt_in',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 11, 14, 20, 29, 13, 125465), null=True, verbose_name='Last opt-in'),
        ),
        migrations.AlterField(
            model_name='siteevent',
            name='last_status_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 14, 20, 29, 13, 125374), verbose_name='Last Status Time'),
        ),
    ]