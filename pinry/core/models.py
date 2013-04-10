import json
import requests
from cStringIO import StringIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models

from django_images.models import Image as BaseImage
from south.modelsinspector import add_introspection_rules
from taggit.managers import TaggableManager

from ..users.models import User


class ImageManager(models.Manager):
    # FIXME: Move this into an asynchronous task
    def create_for_url(self, url):
        file_name = url.split("/")[-1]
        buf = StringIO()
        response = requests.get(url)
        buf.write(response.content)
        obj = InMemoryUploadedFile(buf, 'image', file_name,
                                   None, buf.tell(), None)
        return Image.objects.create(image=obj)


class Image(BaseImage):
    objects = ImageManager()

    class Meta:
        proxy = True


class Pin(models.Model):
    submitter = models.ForeignKey(User)
    board = models.ForeignKey('Board', related_name='pins')
    url = models.URLField(null=True)
    origin = models.URLField(null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ForeignKey(Image, related_name='pin')
    published = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()

    def __unicode__(self):
        return self.url


class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if not isinstance(value, basestring):
            return value
        return json.loads(value, encoding=settings.DEFAULT_CHARSET)

    def get_prep_value(self, value):
        return json.dumps(value)
add_introspection_rules([], ["^pinry\.core\.models\.JSONField"])


class Board(models.Model):
    name = models.CharField(max_length=75)
    description = models.TextField(null=True, blank=True)
    members = models.ManyToManyField(User)
    settings = JSONField(default={})

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (
            ('view_board', 'Can view board'),
        )
