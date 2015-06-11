# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from public_api.models import Tag, Category, User, Artist, Post, Comment, Entry

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.filters import OrderingFilter

from django.db.models import Count


def gen_serializer(name='CustomSerializer', base=ModelSerializer, **kwargs):
    meta = type(str('Meta'), (object,), kwargs)
    return type(str(name), (base,), {'Meta': meta})


class ApiViewSet(ReadOnlyModelViewSet):
    serializers_mapping = {
        'retrieve': ReadOnlyModelViewSet.serializer_class,
        'list': ReadOnlyModelViewSet.serializer_class,
    }

    def get_serializer_class(self):
        return self.serializers_mapping.get(self.action) or\
            super(PostViewSet, self).get_serializer_class()


class TagSerializer(ModelSerializer):
    class Meta:
        exclude = ('posts',)
        model = Tag

class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()

    serializer_class = TagSerializer
    search_fields = ('title',)



class CategoryListSerializer(ModelSerializer):
    class Meta:
        exclude = ('posts',)
        model = Category

class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.all()

    serializer_class = CategoryListSerializer
    search_fields = ('title',)



class CommentViewSet(ReadOnlyModelViewSet):
    queryset = Comment.objects.all()

    serializer_class = gen_serializer(model=Comment)
    filter_fields = ('author', 'post',)
    ordering = ('-date',)



class PostDetailSerializer(ModelSerializer):
    entries = gen_serializer(exclude=('post',), model=Entry)(many=True)
    author = gen_serializer(fields=('id', 'name', 'avatar_url',), model=User)()

    class CommentPostDetailSerializer(ModelSerializer):
        author = gen_serializer(fields=('id', 'name', 'avatar_url',), model=User)()

        class Meta:
            model = Comment
            exclude = ('post',)


    comments = CommentPostDetailSerializer(many=True)
    artists = gen_serializer(fields=('id', 'name', 'avatar_url',), model=Artist)(many=True)
    tags = gen_serializer(exclude=('posts',), model=Tag)(many=True)
    categories = gen_serializer(exclude=('posts',), model=Category)(many=True)


    class Meta:
        model = Post


class PostListSerializer(ModelSerializer):
    entries = gen_serializer(exclude=('post',), model=Entry)(many=True)
    artists = gen_serializer(fields=('id', 'name', 'avatar_url',), model=Artist)(many=True)
    tags = gen_serializer(exclude=('posts',), model=Tag)(many=True)
    categories = CategoryListSerializer(many=True)
    author = gen_serializer(fields=('id', 'name', 'avatar_url',), model=User)()
    number_of_comments = SerializerMethodField()

    def get_number_of_comments(self, obj):
        return obj.comments.count()

    class Meta:
        model = Post


class PostViewSet(ApiViewSet):
    queryset = Post.objects.prefetch_related('artists', 'tags', 'author', 'categories', 'comments', 'entries',).all()
    serializer_class = PostListSerializer
    search_fields = ('title',)
    filter_fields = ('artists', 'author', 'tags', 'categories',)
    ordering = ('-date',)

    serializers_mapping = {
        'retrieve': PostDetailSerializer,
        'list': PostListSerializer,
    }


class ArtistListSerializer(ModelSerializer):
    number_of_posts = SerializerMethodField()

    def get_number_of_posts(self, obj):
        return obj.posts.count()

    class Meta:
        model = Artist


class ArtistViewSet(ReadOnlyModelViewSet):
    queryset = Artist.objects\
    .annotate(number_of_posts=Count('posts'))\
    .prefetch_related('posts', 'posts__entries', 'posts__categories', 'posts__tags', 'posts__artists', 'posts__comments', 'posts__author')\
    .all()
    search_fields = ('name',)
    ordering = ('name',)
    ordering_fields = ('number_of_posts', 'name')

    serializer_class = ArtistListSerializer


class UserOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request)

        if ordering:
            # Skip any incorrect parameters
            ordering = self.remove_invalid_fields(queryset, ordering, view)

        if not ordering:
            # Use 'ordering' attribute by default
            ordering = self.get_default_ordering(view)

        if ordering:
            qs_fields = { x.name for x in queryset.model._meta.fields }

            model_ordering = { x for x in ordering if x.replace('-', '') in qs_fields }

            virtual_ordering = set(ordering) - model_ordering

            new_qs = queryset

            for virtual_field in virtual_ordering:
                if virtual_field in ('number_of_comments', '-number_of_comments',):
                    new_qs = queryset.annotate(number_of_comments=Count('comments'))\
                    .extra(where=('(SELECT COUNT(id) FROM public_api_post WHERE author_id = "public_api_user"."id") >= 1',))\

                elif virtual_field in ('number_of_posts', '-number_of_posts',):
                    new_qs = queryset.annotate(number_of_posts=Count('posts')).filter(number_of_posts__gte=1)

            if len(virtual_ordering) < 1:
                new_qs = queryset.annotate(number_of_posts=Count('posts')).filter(number_of_posts__gte=1)

            return new_qs.order_by(*ordering)

        return queryset

class UserListSerializer(ModelSerializer):
    number_of_comments = SerializerMethodField()
    number_of_posts = SerializerMethodField()

    def get_number_of_comments(self, obj):
        return obj.comments.count()

    def get_number_of_posts(self, obj):
        return obj.posts.count()

    class Meta:
        model = User


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.prefetch_related('posts', 'comments',).all()

    serializer_class = UserListSerializer
    filter_backends = tuple(
            filter(lambda x: not isinstance(x, OrderingFilter), ReadOnlyModelViewSet.filter_backends)
        ) + (UserOrderingFilter,)
    search_fields = ('name',)
    ordering_fields = ('name', 'carma', 'last_visit', 'number_of_comments', 'number_of_posts',)
    ordering = ('name',)
