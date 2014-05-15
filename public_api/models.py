# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from django.db import models


class User(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    reg_date = models.DateField()
    last_visit = models.DateTimeField()
    country = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=255, null=True)
    site = models.CharField(max_length=255, null=True)
    skype = models.CharField(max_length=255, null=True)
    email = models.CharField(max_length=255, null=True)
    carma = models.IntegerField()
    avatar_url = models.CharField(max_length=255)
    description = models.TextField(null=True)


class Artist(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    avatar_url = models.CharField(max_length=255)
    description = models.TextField(null=True)


class Post(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    author = models.ForeignKey(to=User, related_name='posts')
    artists = models.ManyToManyField(to=Artist, related_name='posts')
    description = models.TextField(null=True)
    link = models.CharField(max_length=255, null=True)
    date = models.DateTimeField()
    rating = models.IntegerField()
    color = models.CharField(max_length=255)
    face_image_url = models.CharField(max_length=255)


class Entry(models.Model):
    id = models.IntegerField(primary_key=True)
    big_img_url = models.CharField(max_length=255)
    medium_img_url = models.CharField(max_length=255)
    description = models.TextField(null=True)
    rating = models.IntegerField()
    order = models.SmallIntegerField()
    post = models.ForeignKey(to=Post, related_name='entries')



class Tag(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    posts = models.ManyToManyField(to=Post, related_name='tags')


class Category(models.Model):
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    posts = models.ManyToManyField(to=Post, related_name='categories')


class Comment(models.Model):
    id = models.IntegerField(primary_key=True)
    author = models.ForeignKey(to=User, related_name='comments')
    message = models.TextField()
    date = models.DateTimeField()
    reply_to = models.ForeignKey(to='self', related_name='replies', null=True)
    rating = models.IntegerField()
    post = models.ForeignKey(to=Post, related_name='comments')