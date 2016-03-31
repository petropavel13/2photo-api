from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^v1/', include('public_api.urls')),
]
