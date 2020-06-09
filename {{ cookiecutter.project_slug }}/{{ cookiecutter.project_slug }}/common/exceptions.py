import logging
import traceback
from collections import defaultdict

from django.utils import six
from django.utils.termcolors import colorize
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler as rest_exception_handler

logger = logging.getLogger('main')


def exception_handler(exc, context=None):
    """
    Call REST framework's default exception handler first.
    Return None if the exception can not be handled.
    :param exc:
    :param context:
    :return: Response or None
    """
    message = traceback.format_exc()
    response = rest_exception_handler(exc, context)

    if response is not None and isinstance(exc, BaseAPIBusinessError):
        logger.warning(message)
        response.data['error_code'] = response.data['detail'].code
        return response

    if response is not None and isinstance(exc, BaseAPISystemError):
        logger.error(message)
        response.data['error_code'] = response.data['detail'].code
        return response

    if response is not None:
        return response

    logger.error(message)
    return Response({
        'error_code': BaseAPISystemError.default_code,
        'detail': BaseAPISystemError.default_detail,
    }, status=BaseAPISystemError.status_code)


def format_exception(exception_class):
    return exception_class.__name__, exception_class.default_code


class APIExceptionMeta(type):
    def __new__(cls, name, bases, attrs):
        if not hasattr(cls, 'error_codes'):
            cls.error_codes = defaultdict(list)
            cls.exception_tree = defaultdict(list)

        default_code = attrs.get('default_code', None)
        if default_code is None:
            for b in bases:
                default_code = getattr(b, 'default_code', None)
                if default_code:
                    break

        new_class = type(name, bases, attrs)

        cls.error_codes[default_code].append(new_class)

        for b in bases:
            cls.exception_tree[format_exception(b)].append(format_exception(new_class))
        return new_class

    @classmethod
    def display_exception_tree(cls):
        root = format_exception(APIException)
        indent_last = {}

        def get_indent(indent, last=False):
            result = []
            for i in six.moves.range(indent):
                if i == indent - 1:
                    if not last:
                        result.append('|-- ')
                    else:
                        indent_last[indent - 1] = last
                        result.append('\-- ')
                else:
                    if indent_last.get(i, False):
                        result.append('    ')
                    else:
                        result.append('|   ')

            return result

        def display_node(node, indent, last):
            name, default_code = node

            options = {
                'fg': 'green' if len(cls.error_codes[default_code]) == 1 or indent == 0 else 'red',
                'opts': ('bold',)
            }
            print(''.join(get_indent(indent, last)), colorize(node, **options))

        def recursive_display(node, indent, last):
            display_node(node, indent, last)
            for child in cls.exception_tree[node]:
                recursive_display(child, indent + 1, child == cls.exception_tree[node][-1])

        recursive_display(root, 0, True)


@six.add_metaclass(APIExceptionMeta)
class BaseAPIException(APIException):
    default_code = 2000000000


@six.add_metaclass(APIExceptionMeta)
class BaseAPISystemError(BaseAPIException):
    default_code = 9999
    default_detail = _('Internal system error. Please try again later.')


@six.add_metaclass(APIExceptionMeta)
class BaseAPIBusinessError(BaseAPIException):
    """
    Use this exception to raise a business error but not an error in HTTP semantics.

    .. note::
        This type of exception should be used in business APIs instead of REST APIs.
    """
    default_code = 19999
    status_code = status.HTTP_400_BAD_REQUEST


@six.add_metaclass(APIExceptionMeta)
class FrameworkException(BaseAPISystemError):
    default_detail = _('Framework exception.')
    default_code = 1


@six.add_metaclass(APIExceptionMeta)
class OptimisticConcurrencyControlFailed(BaseAPISystemError):
    """
    Optimistic Concurrency Control failed.
    """
    default_detail = 'Optimistic Concurrency Control failed.'
    default_code = 10


@six.add_metaclass(APIExceptionMeta)
class StubHTTPError(BaseAPISystemError):
    """
    Http request error.
    """
    default_detail = _('HTTP error.')
    default_code = 20


@six.add_metaclass(APIExceptionMeta)
class LoginFailed(BaseAPIBusinessError, NotAuthenticated):
    """
    Login at send_email failed.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Login failed.')
    default_code = 30


@six.add_metaclass(APIExceptionMeta)
class InvalidParameters(BaseAPIBusinessError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Invalid parameters.')
    default_code = 10000


@six.add_metaclass(APIExceptionMeta)
class ObjectNotFound(BaseAPIBusinessError):
    default_detail = _('Object not found.')
    default_code = 10001
