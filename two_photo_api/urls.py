from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'two_photo_api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/', include('public_api.urls')),
    # url(r'^/v1/tags/', ListAPIView.as_view(model=Tag))
)
