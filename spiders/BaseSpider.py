# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from grab import Grab
from grab.spider import Spider, Task
from grab.selector import XpathSelector

from utils import *

import django
django.setup()

from public_api.models import *

import logging

import threading

from django.db import transaction

from multiprocessing.pool import ThreadPool as TP


class ThreadPool(TP):
    # python 2 support

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()


class BaseSpider(Spider):
    BASE_URL = 'http://www.2photo.ru'

    tags_ids_in_db = frozenset(Tag.objects.values_list('id', flat=True).all())
    tags_for_save = []

    categories_ids_in_db = frozenset(Category.objects.values_list('id', flat=True).all())
    categories_for_save = []

    post_ids_in_db = frozenset(Post.objects.values_list('id', flat=True).all())
    posts_for_save = []

    users_ids_in_db = frozenset(User.objects.values_list('id', flat=True).all())
    users_for_parse = set()
    users_for_save = []

    artists_ids_in_db = frozenset(Artist.objects.values_list('id', flat=True).all())
    artists_for_parse = set()
    artists_for_save = []

    user_read_lock = threading.Lock()
    artists_read_lock = threading.Lock()
    tag_read_lock = threading.Lock()
    category_read_lock = threading.Lock()


    def task_post(self, grab, task):
        logging.info('Parsing post %s' % task.url)

        album_el = grab.doc.select('//div[@class="column"]')

        album_desc_el = album_el.select('div[@class="album-desc"]')

        post_title = task.post.get('title') or album_desc_el.select('h1').text()

        description_el = album_desc_el.select('p')
        album_description = description_el.text() if description_el.exists() else None

        author_block = grab.doc.select('//div[@class="author"]')
        link_el = author_block.select('.//a[@class="author-side"]')

        link = link_el.attr('href') if link_el.exists() else None
        author_link = None
        artists_links = []

        author_boxes = author_block.select('.//div[@class="user-box"]')

        if author_boxes.count() > 1:
            boxes = list(map(XpathSelector, author_boxes.node_list()))

            author_link = boxes[0].select('div/a[@class="nickname"]').attr('href')

            artists_links = [ab.select('a').attr('href') for ab in boxes[1:]]

        else:
            author_link = author_boxes.select('.//a[@class="nickname"]').attr('href')

        entries = []

        for entry_el in album_el.select('div[@class="album-thumb"]'):
            entry_name = entry_el.attr('id')
            entry_id = int(entry_name[entry_name.index('-') + 1:])

            a_el = entry_el.select('a')

            entry_big_img_url = a_el.attr('href')
            entry_medium_img_url = a_el.select('img').attr('src')

            entry_text_el = entry_el.select('div')
            entry_text = entry_text_el.text() if entry_text_el.exists() else None

            rate_text = entry_el.select('span[@class="rate"]').text()

            order = entry_el.select('em').text()

            entries.append({
                'id': entry_id,
                'big_img_url': 'http://' + entry_big_img_url[2:],
                'medium_img_url': 'http://' + entry_medium_img_url[2:],
                'description': entry_text,
                'rating': prct_to_int(rate_text),
                'order': order,
            })

        tags = []

        for tag_el in album_el.select('div[h5="Метки:"]/ul/li/a'):
            tag_link = tag_el.attr('href')

            tags.append({
                'id': url_to_id(tag_link),
                'title': tag_el.text(),
            })

        categories = []

        for theme_el in album_el.select('div[h5="Темы:"]/ul/li/a'):
            theme_link = theme_el.attr('href')

            categories.append({
                'id': url_to_id(theme_link),
                'title': theme_el.text(),
            })

        comments = []

        last_level = 1

        last_for_level = {}

        for message_item_el in grab.doc.select('//div[@class="comments"]/div'):
            item_class = message_item_el.attr('class')

            if item_class in ('cl', 'cr',):
                continue

            if message_item_el.select('div[@class="message-text deleted"]').exists():
                vote_text = 0
                user_id = 0
                rating = 0
                message_date = tz.now()
                message = "Комментарий удалён"
            else:
                message_text_el = message_item_el.select('div[@class="message-text "]')
                message_text_el = message_text_el if message_text_el.exists() else message_item_el.select('div[@class="message-text"]')
                message_text = message_text_el.select('p').text()

                rating = prct_to_int(message_item_el.select('span[@class="vote"]/span').text())

                user_id = url_to_id(message_item_el.select('div[@class="user-box"]/a').attr('href'))

                message_date_text = message_text_el.select('em[@class="message-date"]').node().text

                message_date = ru_str_date_to_date_comment(message_date_text)

            current_level = int(item_class[item_class.index('level-') + 6:])

            parent = None

            if current_level > last_level:
                parent = last_for_level[last_level]
            elif current_level < last_level:
                parent = last_for_level.get(current_level - 1)

            comment = {
                'id': int(message_item_el.attr('rel')),
                'rating': rating,
                'user_id': int(user_id),
                'message': message_text,
                'date': message_date,
                'reply_to_id': parent,
            }

            comments.append(comment)

            last_level = current_level
            last_for_level[last_level] = comment['id']


        post_rate = task.post.get('rating') or prct_to_int(album_el.select('div[@class="rate"]').text())

        post_id = int(task.post['id'])

        task.post['id'] = post_id
        task.post['rating'] = int(task.post['rating'])
        task.post['date'] = ru_str_date_to_date_stream(task.post['date'])

        author_id = url_to_id(author_link)

        artists_ids = set(map(url_to_id, artists_links))

        task.post.update({
            'title': post_title,
            'description': album_description,
            'artists_ids': artists_ids,
            'author_id': author_id,
            'link': link,
            'entries': entries,
            'tags': tags,
            'categories': categories,
            'comments': comments,
            'face_image_url': 'http://' + task.post['image'][2:],
            'rating': post_rate,
        })

        self.posts_for_save.append(task.post)

        users_to_create = { c['user_id'] for c in comments if c['user_id'] != 0 } | { author_id }

        # import pudb; pudb.set_trace()

        with self.user_read_lock:
            users_to_create -= self.users_ids_in_db
            users_to_create -= self.users_for_parse
            users_to_create -= { u['id'] for u in self.users_for_save }

            self.users_for_parse |= users_to_create

        for u in users_to_create:
            yield Task('user', self.BASE_URL + '/ru/profile/%d' % u, user_id=u)


        artists_to_create = set(artists_ids) # clone

        with self.artists_read_lock:
            artists_to_create -= self.artists_ids_in_db
            artists_to_create -= self.artists_for_parse
            artists_to_create -= { a['id'] for a in self.artists_for_save }

            self.artists_for_parse |= artists_to_create

        for a in artists_to_create:
            yield Task('artist', self.BASE_URL + '/ru/artist/%d' % a, artist_id=a)


        tags_to_create = { c['id'] for c in tags }

        with self.tag_read_lock:
            tags_to_create -= self.tags_ids_in_db
            tags_to_create -= { t['id'] for t in self.tags_for_save }

            self.tags_for_save.extend(filter(lambda t: t['id'] in tags_to_create, tags))


        categories_to_create = { c['id'] for c in categories }

        with self.category_read_lock:
            categories_to_create -= self.categories_ids_in_db
            categories_to_create -= { c['id'] for c in self.categories_for_save }

            self.categories_for_save.extend(filter(lambda x: x['id'] in categories_to_create, categories))

    def task_user(self, grab, task):
        logging.info('Parsing user %s' % task.url)

        user_info_el = grab.doc.select('//div[@class="user-info-box"]')

        user_box_el = grab.doc.select('//div[@class="user-box"]')

        img_url = user_box_el.select('img').attr('src')

        user_name = user_info_el.select('h1').text()

        carma = int(user_box_el.select('.//span[@class="carma"]').text())

        next_key = None

        reg_date = None
        last_visit = None
        country = None
        city = None
        site = None
        email = None
        skype = None
        description = None

        for info_el in user_info_el.select('dl/*'):
            if info_el.node().tag == 'dt':
                next_key = info_el.text()
                continue

            v = info_el.text()

            if next_key == 'Дата регистрации:':
                reg_date = ru_str_date_to_date_reg(v)
            elif next_key == 'Последнее посещение:':
                last_visit = ru_str_date_to_date_last_visit(v)
            elif next_key == 'Страна:':
                country = v
            elif next_key == 'Город:':
                city = v
            elif next_key == 'WWW:':
                site = v
            elif next_key == 'E-mail:':
                email = v
            elif next_key == 'Skype:':
                skype = v
            elif next_key == '':
                description = v


        self.users_for_save.append({
                'id': task.user_id,
                'name': user_name,
                'reg_date': reg_date,
                'last_visit': last_visit,
                'country': country,
                'city': city,
                'site': site,
                'email': email,
                'carma': carma,
                'skype': skype,
                'description': description,
                'avatar_url': 'http://' + img_url[2:],
        })


    def task_artist(self, grab, task):
        logging.info('Parsing artist %s' % task.url)

        avatar_url = grab.doc.select('//div[@class="user-box"]/img').attr('src')
        info_el = grab.doc.select('//div[@class="exhibit-header-desc"]')
        name = info_el.select('h1').text()
        description_el = info_el.select('.//dd')
        description_text = description_el.text() if description_el.exists() else None

        self.artists_for_save.append({
            'id': task.artist_id,
            'name': name,
            'avatar_url': 'http://' + avatar_url[2:],
            'description': description_text,
        })


    def save_tags(self):
        logging.info('Saving tags...')

        if len(self.tags_for_save) > 0:
            with transaction.atomic():
                bulk_save_by_chunks(dicts_to_model_instances(self.tags_for_save, Tag), Tag, 4096)

        self.tags_for_save = []

        logging.info('Saving tags done.')


    def save_categories(self):
        logging.info('Saving categories...')

        if len(self.categories_for_save) > 0:
            with transaction.atomic():
                bulk_save_by_chunks(dicts_to_model_instances(self.categories_for_save, Category), Category, 4096)

        self.categories_for_save = []

        logging.info('Saving categories done.')


    def save_users(self):
        logging.info('Saving users...')

        try:
            User.objects.get(id=0)
        except User.DoesNotExist:
            User.objects.create(id=0, name='', reg_date=tz.now(), last_visit=tz.now(), carma=0, avatar_url='')

        if len(self.users_for_save) > 0:
            with transaction.atomic():
                bulk_save_by_chunks(dicts_to_model_instances(self.users_for_save, User), User, 512)

        self.users_for_save = []
        self.users_for_parse = set()

        logging.info('Saving users done.')


    def save_artists(self):
        logging.info('Saving artists...')

        if len(self.artists_for_save) > 0:
            with transaction.atomic():
                bulk_save_by_chunks(dicts_to_model_instances(self.artists_for_save, Artist), Artist, 2048)

        self.artists_for_save = []
        self.artists_for_parse = set()

        logging.info('Saving artists done.')


    def save_posts(self):
        logging.info('Saving posts...')

        all_users = { u.id: u for u in User.objects.all() }
        all_artists = { a.id: a for a in Artist.objects.all() }

        [p.update(author=all_users[p['author_id']]) for p in self.posts_for_save]

        with transaction.atomic():
            bulk_save_by_chunks(dicts_to_model_instances(self.posts_for_save, Post), Post, 1024)

        # cache for next save operations

        self.all_posts_mapping = { p.id: p for p in Post.objects.only('id').all() }

        logging.info('Saving posts done.')


    def save_posts_artists(self):
        logging.info('Saving posts-artists...')

        all_artists_mapping = { a.id: a for a in Artist.objects.only('id').all() }

        with transaction.atomic():
            for post in self.posts_for_save:
                raw_post_artists = set(post['artists_ids'])

                self.all_posts_mapping[post['id']].artists.add(*[all_artists_mapping[a] for a in raw_post_artists])

        logging.info('Saving posts-artists done')


    def save_posts_tags(self):
        logging.info('Saving posts-tags...')

        all_tags_mapping = { t.id: t for t in Tag.objects.only('id').all() }

        with transaction.atomic():
            for post in self.posts_for_save:
                raw_post_tags = { t['id'] for t in post['tags'] }

                self.all_posts_mapping[post['id']].tags.add(*[all_tags_mapping[t] for t in raw_post_tags])

        logging.info('Saving posts-tags done')


    def save_posts_categories(self):
        logging.info('Saving posts-categories...')

        all_categories_mapping = { c.id : c for c in Category.objects.only('id').all() }

        with transaction.atomic():
            for post in self.posts_for_save:
                raw_post_categories = { c['id'] for c in post['categories'] }

                self.all_posts_mapping[post['id']].categories.add(*[all_categories_mapping[c] for c in raw_post_categories])

        logging.info('Saving posts-categories done')


    def save_entries(self):
        logging.info('Saving entries...')

        entries_for_save = []

        for post in self.posts_for_save:
            r_post = self.all_posts_mapping[post['id']]
            entries = post['entries']

            [e.update(post=r_post) for e in entries]

            entries_for_save.extend(entries)

        with transaction.atomic():
            bulk_save_by_chunks(dicts_to_model_instances(entries_for_save, Entry), Entry, 1024)

        logging.info('Saving entries done')


    def save_comments(self):
        logging.info('Saving comments...')

        users_mapping = { u.id: u for u in User.objects.all() }

        def save_comments_hierarchy(post, head_comments, other_comments):
            comments_mapping = {}

            for c in head_comments:
                c.update(post=post, author=users_mapping[c['user_id']], reply_to=c.get('reply_to'))
                cm = dict_to_model_instance(c, Comment)
                # cm.save(force_insert=True)
                comments_mapping.update({cm.id: cm})


            if len(comments_mapping) > 0:
                comments = comments_mapping.values()

                Comment.objects.bulk_create(comments)

                to_save = []
                other = list(other_comments)

                for c in comments:
                    reply_to_current = list(filter(lambda x: x['reply_to_id'] == c.id, other))

                    for leaf in reply_to_current:
                        leaf['reply_to'] = c

                    to_save.extend(reply_to_current)

                save_comments_hierarchy(post, to_save, filter(lambda x: x['reply_to_id'] not in comments_mapping, other))

        with transaction.atomic():
            for post in self.posts_for_save:
                comments = post['comments']

                to_save = filter(lambda x: x['reply_to_id'] is None, comments)
                other = filter(lambda x: x['reply_to_id'] is not None, comments)

                save_comments_hierarchy(self.all_posts_mapping[post['id']], to_save, other)

        logging.info('Saving comments done')


    def save_all(self):
        # self.save_tags()
        # self.save_categories()
        # self.save_users()
        # self.save_artists()


        with ThreadPool(processes=2) as executor:
            executor.apply_async(self.save_tags)
            executor.apply_async(self.save_categories)
            executor.apply_async(self.save_users)
            executor.apply_async(self.save_artists)

            executor.close()
            executor.join()


        self.save_posts()


        # self.save_posts_tags()
        # self.save_posts_categories()
        # self.save_posts_artists()
        # self.save_entries()
        # self.save_comments()

        with ThreadPool(processes=2) as executor:
            executor.apply_async(self.save_posts_tags)
            executor.apply_async(self.save_posts_categories)
            executor.apply_async(self.save_posts_artists)
            executor.apply_async(self.save_entries)
            executor.apply_async(self.save_comments)

            executor.close()
            executor.join()
