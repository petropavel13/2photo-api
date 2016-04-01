# -*- coding: utf-8 -*-

from __future__ import unicode_literals # py2

from datetime import datetime

from django.utils import timezone as tz
from django.utils.timezone import is_naive, make_aware

msk_tz = tz.pytz.timezone('Europe/Moscow')

date_mapping = {
    'января': '1',
    'февраля': '2',
    'марта': '3',
    'апреля': '4',
    'мая': '5',
    'июня': '6',
    'июля': '7',
    'августа': '8',
    'сентября': '9',
    'октября': '10',
    'ноября': '11',
    'декабря': '12',
}

def to_msk_datetime(datetime):
    if is_naive(datetime):
        return datetime.replace(tzinfo=msk_tz)
    elif datetime.tzinfo == msk_tz:
        return datetime
    else:
        return tz.localtime(datetime, msk_tz)

def if_not_none(func):
    return lambda arg: None if arg is None else func(arg)


@if_not_none
def prct_to_int(percent):
    return int(percent[:percent.index('%')])


@if_not_none
def url_to_id(url):
    str_id = url[url.rindex('/') + 1:]

    return int(str_id) if len(str_id) > 0 else None


def ru_str_date_to_date_stream(ru_date):
    new_date = ru_date

    for ru, en in date_mapping.items():
        new_date = new_date.replace(ru, en)

    py2_date = new_date.encode('utf-8')

    py3_format = '%d %m %Y г. %H:%M'
    py2_format = py3_format.encode('utf-8')

    date = datetime.strptime(py2_date if isinstance(py2_date, str) else new_date,
                            py2_format if isinstance(py2_format, str) else py3_format)

    return to_msk_datetime(date)


def ru_str_date_to_date_comment(ru_date):
    new_date = ru_date

    for ru, en in date_mapping.items():
        new_date = new_date.replace(ru, en)

    str_date = new_date.replace('\n          ', '').replace('                      ', '')
    py3_date = '0' + str_date if str_date.index(':') == 1 else str_date
    py2_date = py3_date.encode('utf-8')

    py3_format = '%H:%M,%d %m %Y г.'
    py2_format =  py3_format.encode('utf-8')


    date = datetime.strptime(py2_date if isinstance(py2_date, str) else py3_date,
                            py2_format if isinstance(py2_format, str) else py3_format)

    return to_msk_datetime(date)


def ru_str_date_to_date_reg(ru_date):
    new_date = ru_date

    for ru, en in date_mapping.items():
        new_date = new_date.replace(ru, en)

    return to_msk_datetime(datetime.strptime(new_date, '%d %m %Y'))


def ru_str_date_to_date_last_visit(ru_date):
    new_date = ru_date

    for ru, en in date_mapping.items():
        new_date = new_date.replace(ru, en)

    date = datetime.strptime(new_date, '%d %m %Y, %H:%M')

    return to_msk_datetime(date)


def clean_dict_for_model(dict_obj, dj_model):
    return { f.name : dict_obj[f.name] for f in dj_model._meta.fields }


def dict_to_model_instance(dict_obj, dj_model):
    return dj_model( **clean_dict_for_model(dict_obj, dj_model) )


def bulk_create_by_chunks(iterable_objects, dj_model, chunk_size=1024):
    buffer = [None] * chunk_size

    next_idx = 0

    for obj in iterable_objects:
        buffer[next_idx] = obj

        next_idx += 1

        if next_idx % chunk_size == 0:
            dj_model.objects.bulk_create(buffer)

            next_idx = 0


    dj_model.objects.bulk_create(buffer[0:next_idx])


def namedtuples_to_model_instances_generator(namedtuples, dj_model):
    for namedtuple in namedtuples:
        yield dict_to_model_instance(namedtuple._asdict(), dj_model)


def bulk_save_namedtuples(namedtuples, dj_model, chunk_size=1024):
    model_instances_generator = namedtuples_to_model_instances_generator(namedtuples, dj_model)
    bulk_create_by_chunks(model_instances_generator, dj_model, chunk_size)
