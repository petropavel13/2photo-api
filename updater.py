#!/usr/bin/env python

# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "two_photo_api.settings")


from grab import Grab
from grab.selector import XpathSelector

from spiders import UpdateSpider


spider = UpdateSpider(thread_number=8, network_try_limit=64, task_try_limit=32)
spider.grab_config.update(timeout=60, connect_timeout=30)
spider.run()

spider.save_all()