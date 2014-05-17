import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'two_photo_api.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
