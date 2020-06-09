import logging
import urllib.request

from cloudinary import CloudinaryImage
from cloudinary.uploader import upload
from django.core.files import File
from django.utils.timezone import now

from common.utils import log_execution_time, datetime_to_utc_unix

logger = logging.getLogger('main')


class Storage:
    @classmethod
    def _download_url(cls, url: str):
        result = urllib.request.urlretrieve(url)
        return result[0]

    @classmethod
    @log_execution_time
    def _save_file(cls, file: [File, str], public_id: str = None):
        params = {
            'file': file,
            'overwrite': True,
        }
        if public_id:
            params['public_id'] = public_id

        result = upload(**params)
        return result['public_id'], result['version']

    @classmethod
    @log_execution_time
    def _save_file_from_url(cls, url: str, public_id: str = None):
        return cls._save_file(cls._download_url(url=url), public_id=public_id)

    @classmethod
    def get_download_url(cls, public_id: str, version: int, width: int = None, height: int = None):
        transformation = {}
        if width and height:
            transformation['width'] = width
            transformation['height'] = height
            transformation['crop'] = "fill"

        current_ts = datetime_to_utc_unix(now())
        if not version:
            version = current_ts
        if not transformation:
            return CloudinaryImage(public_id=public_id, version=version).build_url()
        return CloudinaryImage(public_id=public_id, version=version).build_url(transformation=transformation)

    @classmethod
    def save_picture_for_object(cls, key: str, file: [File, str], directory='default'):
        logger.info('directory=%s,key=%s', directory, key)
        public_id = '%s/%s' % (directory, key)
        return cls._save_file(file=file, public_id=public_id)

    @classmethod
    def save_picture_url_for_object(cls, key: str, url: str, directory='default'):
        logger.info('url=%s,directory=%s,key=%s', url, directory, key)
        public_id = '%s/%s' % (directory, key)
        return cls._save_file_from_url(url=url, public_id=public_id)
