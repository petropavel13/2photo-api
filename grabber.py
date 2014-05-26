#!/usr/bin/env python

# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "two_photo_api.settings")

from public_api.models import *

from django.db import connection
cursor = connection.cursor()

[cursor.execute('TRUNCATE "%s" RESTART IDENTITY CASCADE;' % m._meta.db_table)\
for m in (User, Artist, Post, Entry, Tag, Category, Comment,)]

cursor.close()

from spiders import InitialSpider

spider = InitialSpider(thread_number=8, network_try_limit=64, task_try_limit=32)
spider.grab_config.update(timeout=60, connect_timeout=30)
spider.run()

spider.save_all()
