# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from grab import Grab
from spiders import BaseSpider
from grab.spider import Task

import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.FileHandler('/tmp/parse.log'))

from grab.tools.logs import default_logging
default_logging()

from public_api.models import Post

class UpdateSpider(BaseSpider):
    """Spider for initial data grabbing"""

    BASE_STREAM_URL = BaseSpider.BASE_URL + '/ru/post/stream.json'

    initial_urls = (BASE_STREAM_URL,)

    def task_initial(self, grab, task):
        posts = { int(p['id']): p for p in grab.response.json['posts'] }
        sorted_posts = sorted(posts.values(), key=lambda x: int(x['id']))
        last_post_id = int(list(reversed(sorted_posts))[0]['id'])
        max_offset = 0

        last_post_id_in_db = Post.objects.order_by('-id').first().id

        if last_post_id_in_db == last_post_id:
            logging.info('Up to date')
        else:
            g = Grab(connect_timeout=30, timeout=60)

            while True:
                posts = { int(p['id']): p for p in g.go(task.url + ('?limit=10&offset=%d' % max_offset)).json['posts'] }

                if last_post_id_in_db in posts:
                    break
                else:
                    max_offset += 10


            all_posts = []


            # all_posts = g.go(task.url + ('?limit=256&offset=4096')).json['posts']

            for x in range(0, max_offset + 10, 10):
                logging.info('Loading stream posts %d-%d (%d) time:%d' % (max_offset - x, max_offset - x - 256,  max_offset, g.response.total_time,))
                all_posts.extend(g.go(task.url + ('?limit=10&offset=%d' % x)).json['posts'])

            # yield Task('post', url=self.BASE_URL + '/ru/post/32033', post=list(filter(lambda x: x['id'] == '32033', all_posts))[0])
            # yield Task('post', url=self.BASE_URL + '/ru/post/31279', post=list(filter(lambda x: x['id'] == '31279', all_posts))[0])

            post_ids_in_db = frozenset(Post.objects.values_list('id', flat=True).all())

            for post in all_posts:
                if int(post['id']) not in post_ids_in_db:
                    yield Task('post', url=self.BASE_URL + post['link'], post=post)