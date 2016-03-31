# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from collections import namedtuple


SpiderEntry = namedtuple('SpiderEntry',
    ['id',
    'big_img_url',
    'medium_img_url',
    'description',
    'rating',
    'order',
    # model-only fields
    'post',]
    )

SpiderTag = namedtuple('SpiderTag',
    ['id',
    'title',]
    )

SpiderCategory = namedtuple('SpiderCaregory',
    ['id',
    'title',]
    )

SpiderComment = namedtuple('SpiderComment',
    ['id',
    'rating',
    'user_id',
    'message',
    'date',
    'reply_to_id',
    # model-only fields
    'post',
    'author',
    'reply_to',]
    )

SpiderPost = namedtuple('SpiderPost',
    ['id',
    'title',
    'description',
    'artists_ids',
    'author_id',
    'link',
    'date',
    'entries',
    'tags',
    'categories',
    'comments',
    'face_image_url',
    'rating',
    'color',
    # model-only fields
    'author',]
    )

SpiderUser = namedtuple('SpiderUser',
    ['id',
    'name',
    'reg_date',
    'last_visit',
    'country',
    'city',
    'site',
    'email',
    'carma',
    'skype',
    'description',
    'avatar_url',]
    )

SpiderArtist = namedtuple('SpiderArtist',
    ['id',
    'name',
    'avatar_url',
    'description',]
    )
