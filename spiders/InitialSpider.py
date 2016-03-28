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


class InitialSpider(BaseSpider):
    """Spider for initial data grabbing"""

    BASE_STREAM_URL = BaseSpider.BASE_URL + '/ru/post/stream.json'

    initial_urls = (BASE_STREAM_URL,)


    def task_initial(self, grab, task):
        sorted_posts = sorted(grab.response.json['posts'], key=lambda x: int(x['id']))
        past_jump = max_offset = int(sorted_posts[0]['id'])

        g = self.create_grab_instance()

        while True:
            cnt = len(g.go(task.url + ('?limit=10&offset=%d' % max_offset)).json['posts'])

            logging.debug('Searching max offset. current: %d; jump_size: %d; count: %d', (max_offset, past_jump, cnt))

            if cnt > 0 and cnt < 10:
                break
            elif cnt > 0:
                max_offset += past_jump
            else:
                past_jump = past_jump // 2
                max_offset -= past_jump

        all_posts = []

        # all_posts.extend(g.go('http://www.2photo.ru/ru/post/stream.json?limit=8&offset=190').json['posts'])

        # all_posts = g.go(task.url + ('?limit=512&offset=1024')).json['posts']
        # all_posts.extend(g.go(task.url + ('?limit=512&offset=512')).json['posts'])

        # all_posts = g.go(task.url + ('?limit=64&offset=900')).json['posts']
        # yield Task('post', url=self.BASE_URL + '/ru/post/31279', post=list(filter(lambda x: x['id'] == '31279', all_posts))[0])

        for x in range(0, max_offset, 256):
            logging.info('Loading stream posts %d-%d (%d) time:%d' % (max_offset - x, max_offset - x - 256,  max_offset, g.response.total_time,))
            all_posts.extend(g.go(task.url + ('?limit=256&offset=%d' % x)).json['posts'])


        for post in all_posts:
            yield Task('post', url=self.BASE_URL + post['link'], post=post)

