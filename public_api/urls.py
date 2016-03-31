# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)


from django.conf.urls import include, url

from public_api.rest import TagViewSet, CategoryViewSet, UserViewSet, ArtistViewSet, CommentViewSet, PostViewSet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(prefix=r'tags', viewset=TagViewSet)
router.register(prefix=r'categories', viewset=CategoryViewSet)
router.register(prefix=r'authors', viewset=UserViewSet)
router.register(prefix=r'artists', viewset=ArtistViewSet)
router.register(prefix=r'comments', viewset=CommentViewSet)
router.register(prefix=r'posts', viewset=PostViewSet)


urlpatterns = [
	url('', include(router.urls)),
]
