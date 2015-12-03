# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_helpers


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='options',
            field=model_helpers.KeyValueField(default=b'', help_text=b'Set options using key=value format. i.e. password=123', blank=True),
        ),
    ]
