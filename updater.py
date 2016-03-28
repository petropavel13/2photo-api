#!/usr/bin/env python

# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "two_photo_api.settings")


from spiders import UpdateSpider

spider = UpdateSpider()
spider.run()

spider.save_all()