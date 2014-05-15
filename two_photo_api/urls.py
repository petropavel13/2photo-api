from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from public_api.rest import TagViewSet, CategoryViewSet, UserViewSet, ArtistViewSet, CommentViewSet, PostViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(prefix=r'tags', viewset=TagViewSet)
router.register(prefix=r'categories', viewset=CategoryViewSet)
router.register(prefix=r'authors', viewset=UserViewSet)
router.register(prefix=r'artists', viewset=ArtistViewSet)
router.register(prefix=r'comments', viewset=CommentViewSet)
router.register(prefix=r'posts', viewset=PostViewSet)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'two_photo_api.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/', include(router.urls)),
    # url(r'^/v1/tags/', ListAPIView.as_view(model=Tag))
)
