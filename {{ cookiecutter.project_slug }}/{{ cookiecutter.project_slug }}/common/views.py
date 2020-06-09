import logging
import time
import json
import six
from rest_framework import views, exceptions

from common.exceptions import InvalidParameters

HTTP_METHOD_SERIALIZER_CLASS_NAME_FORMAT = 'http_method_%s_serializer_class'
CUSTOMIZED_HTTP_METHODS = ('get', 'post', 'put')

logger = logging.getLogger('main')
__all__ = ['BaseAPIView']


def format_errors(errors):
    """
    Use this function to format serializer.errors.

    :param errors:
    :return: A `\n` separated string which can be displayed properly as a human-readable error message.
    """
    messages = []
    for field, error_detail in errors.items():
        if isinstance(error_detail, dict):
            error_message = format_errors(error_detail)
        else:
            error_message = ', '.join([str(e) for e in error_detail])

        messages.append(': '.join([str(field), error_message]))

    return '\n'.join(messages)


def construct_validate_serializer_wrapper(method, origin_func):
    def validate_serializer_wrapper(_func):
        def inner(self, request, *args, **kwargs):
            serializer_class_name = HTTP_METHOD_SERIALIZER_CLASS_NAME_FORMAT % method.lower()
            if hasattr(self, serializer_class_name):
                serializer_class = getattr(self, serializer_class_name)
                if serializer_class is None:
                    return _func(self, request, None, *args, **kwargs)
            else:
                try:
                    serializer_class = self.get_serializer_class()
                except (AssertionError, AttributeError):
                    if method.lower() == 'get':
                        return _func(self, request, None, *args, **kwargs)
                    raise exceptions.APIException(
                        'For http method, you must define a serializer class which is used to validate the input data.'
                    )

            # There is no `partial` in the initialization params, which means do not support partial update for now.
            if method == 'get':
                serializer = serializer_class(data=request.query_params)
            else:
                serializer = serializer_class(data=request.data)

            if not serializer.is_valid():
                raise InvalidParameters(detail=format_errors(serializer.errors))

            return _func(self, request, serializer, *args, **kwargs)

        return inner

    return validate_serializer_wrapper(origin_func)


def default_get_serializer_class(self):
    """
    Return the class to use for the serializer.
    Defaults to using `self.serializer_class`.

    You may want to override this if you need to provide different
    serializations depending on the incoming request.

    (Eg. admins get full serialization, others get basic serialization)
    """
    assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, a `http_method_XXXX_serializer_class`, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
    )

    return self.serializer_class


def get_serializer_class_wrapper(func):
    """
    The `func` here is the original `get_serializer_class` function.

    :param func:
    :return:
    """

    def get_serializer_class(self, *args, **kwargs):
        """
        Return serializer_class depending on the http method, or return the self.serializer_class

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        get_serializer_class_func = func or default_get_serializer_class
        if self.request and self.request.method:
            method = self.request.method

            serializer_class_name = HTTP_METHOD_SERIALIZER_CLASS_NAME_FORMAT % method.lower()
            if not hasattr(self, serializer_class_name):
                return get_serializer_class_func(self, *args, **kwargs)
            return getattr(self, serializer_class_name)

        return get_serializer_class_func(self, *args, **kwargs)

    return get_serializer_class


class SerializerValidationMeta(type):
    """
    If the view has the http method handlers(get, post, put and so on), by default the serializer class should be
    implemented and assigned as an attribute of the view class.

    If the serializer classes do not exist, an error will be raised.
    If the serializer classes are assigned to be None explicit, that means do not need to use the serializer class
    to validate input data.
    """

    def __new__(mcs, name, bases, attrs):
        new_class = super(SerializerValidationMeta, mcs).__new__(mcs, name, bases, attrs)

        # The instance of SerializerValidationMeta here is BaseAPIView.
        # If the class is not the subclass of BaseAPIView, just return the new_class
        parents = [b for b in bases if isinstance(b, SerializerValidationMeta)]
        if not parents:
            return new_class

        for method in CUSTOMIZED_HTTP_METHODS:
            if hasattr(new_class, method):
                origin_func = getattr(new_class, method)
                new_func = construct_validate_serializer_wrapper(method, origin_func)
                setattr(new_class, method, new_func)

        # overwrite the `get_serializer_class` function.
        origin_get_serializer_class = getattr(new_class, 'get_serializer_class', None)
        setattr(new_class, 'get_serializer_class', get_serializer_class_wrapper(origin_get_serializer_class))

        return new_class


class BaseAPIView(six.with_metaclass(SerializerValidationMeta, views.APIView)):
    @classmethod
    def get_field(cls, obj, field):
        if not hasattr(obj, field):
            return '...'
        try:
            data = json.dumps(getattr(obj, field))
        except TypeError:
            return '...'
        if len(data) > 4096:
            return '...'
        return data

    def dispatch(self, request, *args, **kwargs):
        start = time.time()
        response = super(BaseAPIView, self).dispatch(request, *args, **kwargs)
        duration = int((time.time() - start) * 1000)
        # self.request is the REST framework request, instead of Django HttpRequest
        logger.info(
            'ACCESS_LOG|view=[%s], uri=[%s], user=[%s], method=[%s], duration=[%s ms], query_params=[%s],'
            ' data=[%s], response_status=[%s], response_content=[%s]',
            self.get_view_name(),
            self.request._request.build_absolute_uri(self.request._request.get_full_path()),
            self.request.user,
            self.request.method,
            duration,
            self.get_field(self.request, 'query_params'),
            self.get_field(self.request, 'data'),
            response.status_code,
            self.get_field(self.response, 'data'),
        )
        return response
