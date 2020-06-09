# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json
import logging
import math
import random
import time
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
import gevent
import pytz
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import FieldFile
from django.forms import model_to_dict
from django.utils import timezone
from django.utils.timezone import localtime

RANDOM_CHARACTER_SET = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
RANDOM_DIGIT_SET = '1234567890'

logger = logging.getLogger('main')


def log_execution_time(func):
    tag = func.__name__

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug('%s|enter', tag)

        ret = func(*args, **kwargs)

        end_time = time.time()
        elapsed = end_time - start_time
        logger.debug('%s|exit|elapsed=%s', tag, elapsed)

        return ret

    return wrapper


def date_to_datetime(date):
    return localtime().replace(year=date.year, month=date.month, day=date.day,
                               hour=0, minute=0, second=0, microsecond=0)


def datetime_to_utc_unix_ms(datetime_object):
    if not datetime_object:
        return None
    unix_time = datetime.datetime(1970, 1, 1, 0, 0).replace(tzinfo=pytz.utc)
    unix_time = (datetime_object - unix_time).total_seconds()
    unix_time = int(unix_time) * 1000
    return unix_time


def datetime_to_utc_unix(datetime_object):
    if not datetime_object:
        return 0
    unix_time = datetime.datetime(1970, 1, 1, 0, 0).replace(tzinfo=pytz.utc)
    unix_time = (datetime_object - unix_time).total_seconds()
    return int(unix_time)


def utc_unix_to_current_datetime(utc_unix_time):
    if not utc_unix_time:
        return None
    utc_datetime = timezone.datetime.utcfromtimestamp(utc_unix_time / 1000)
    utc_datetime = timezone.make_aware(utc_datetime, pytz.utc)
    current_tz = timezone.get_current_timezone()
    return current_tz.normalize(utc_datetime)


def get_content_type_for_model(obj):
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


def generate_result_from_paginator(
        model_cls, serializer_cls,
        search_options=None, sort_options=(),
        start_id=None, page_number=1, page_size=20
):
    qs = model_cls.objects.order_by('-id')

    if sort_options:
        for option in sort_options:
            qs = qs.order_by(option)

    if search_options:
        qs = qs.filter(**search_options)

    # Note:
    # This line will override the behavior of paginator, so we can not trust the paginator.count as total records
    if start_id:
        qs = qs.filter(id__lt=start_id)
        page_number = 1

    paginator = Paginator(qs, page_size, allow_empty_first_page=True)
    page = paginator.get_page(page_number)

    has_next = page.has_next()
    data = serializer_cls(instance=page.object_list, many=True).data

    last_id = list(page.object_list)[-1].id if data else None
    return {
        'has_next': has_next,
        'data': data,
        'last_id': last_id,
    }


def generate_result_from_paginator_for_admin_portal(model_cls, serializer_cls, search_options=None, sort_options=(),
                                                    page_number=1, page_size=20
                                                    ):
    qs = model_cls.objects.order_by('-id')

    if sort_options:
        for option in sort_options:
            qs = qs.order_by(option)

    if search_options:
        qs = qs.filter(**search_options)

    paginator = Paginator(qs, page_size, allow_empty_first_page=True)
    page = paginator.get_page(page_number)

    data = serializer_cls(instance=page.object_list, many=True).data

    return {
        'data': data,
        'total': paginator.count,
    }


def compare_data(instance_field, input_data):
    if isinstance(instance_field, FieldFile):
        if instance_field.name != input_data:
            return instance_field.name, input_data

    return instance_field, input_data


def diff(instance, input_data):
    changes = {}
    for name, value in input_data.items():
        if hasattr(instance, name) and input_data[name] != getattr(instance, name):
            _from, _to = compare_data(getattr(instance, name), input_data[name])
            if _from == _to:
                continue

            changes[name] = {
                'from': _from,
                'to': _to,
            }
    return changes


def get_diff(instance, input_data):
    from_data = {}
    to_data = {}
    changes = {}
    for name, value in input_data.items():
        if hasattr(instance, name) and input_data[name] != getattr(instance, name):
            _from, _to = compare_data(getattr(instance, name), input_data[name])
            if _from == _to:
                continue
            changes[name] = {
                'from': _from,
                'to': _to,
            }
            from_data[name] = _from
            to_data[name] = _to
    return from_data, to_data, changes


def get_valid_fields_for_model(model_cls, data_map):
    valid_field_names = [f.name for f in model_cls._meta.get_fields()]
    return {name: data_map[name] for name in valid_field_names if name in data_map}


def dump_to_json(data):
    return json.dumps(data, cls=DjangoJSONEncoder)


def dump_instance_to_json(instance):
    return json.dumps(model_to_dict(instance), cls=DjangoJSONEncoder)


def make_change_message(instance, input_data):
    changes = diff(instance, input_data)
    if changes:
        return dump_to_json(changes)
    return ''


def random_string(length, allowed_chars=RANDOM_CHARACTER_SET):
    max_index = len(allowed_chars) - 1
    return ''.join([allowed_chars[random.randint(0, max_index)] for _ in range(length)])


def random_digit(length):
    return random_string(length, allowed_chars=RANDOM_DIGIT_SET)


def get_list_result_from_paginator(queryset, page_size, page_number, serializer_cls):
    paginator = Paginator(queryset, page_size, allow_empty_first_page=True)
    page = paginator.get_page(page_number)

    has_next = page.has_next()
    data = serializer_cls(instance=page.object_list, many=True).data
    last_id = data[-1].get('id') if data else None

    return {
        'has_next': has_next,
        'data': data,
        'last_id': last_id
    }


def round_up(n: Decimal, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier


def money_round_up(value: Decimal, level=3):
    multiplier = Decimal(math.pow(10, level))
    return Decimal(value/multiplier).quantize(Decimal(1.0), rounding=ROUND_HALF_UP) * multiplier


def get_update_data(data_field, db_field, data):
    value = data.get(data_field)
    if value:
        return {
            db_field: value
        }
    return {}


def should_asynchronous(func):
    """
    Decorator for functions that should be executed in asynchronous way, usually for IO tasks, calling external services
    like sending emails, ...
    Asynchronous is default behaviour of decorated function, but can still execute synchronously.

    Examples:
        @should_asynchronous
        def foo():
            import time
            time.sleep(1000) # do something extremely long
            return

        foo() -> execute function in asynchronous way (by default)
        foo(should_async=False) -> execute function in synchronous way

    :param func:
    :return:
    """
    def exception_logging_wrapper(func, *args, **kwargs):
        try:
            logger.info('begin|async|%s.%s', func.__module__, func.__name__)
            func(*args, **kwargs)
            logger.info('end|async|%s.%s', func.__module__, func.__name__)
        except Exception as e:
            # catch for all kinds of Exception that are not handled by `func` in order to log traceback
            logger.exception('error|async|%s.%s', func.__module__, func.__name__)
            raise e

    def inner(*args, **kwargs):
        should_async = kwargs.pop('should_async', True)
        if not should_async:
            return func(*args, **kwargs)
        gevent.spawn(exception_logging_wrapper, func, *args, **kwargs)
        # switch the execution
        gevent.sleep(0)
        return None

    return inner


def update_instance(instance, to_data):
    # Update object in memory to keep it match with db
    for field, value in to_data.items():
        setattr(instance, field, value)
