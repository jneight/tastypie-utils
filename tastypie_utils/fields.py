# coding=utf-8

import base64
import re
import mimetypes

from django.core.files.uploadedfile import SimpleUploadedFile

from tastypie.bundle import Bundle
from tastypie import fields
from tastypie.exceptions import ApiFieldError


class Base64FileField(fields.FileField):

    """
    A base64 file-related field.

    Image is sent by client in POST/PUT as a base64 string.
    GET responses will be the path stored

    """

    dehydrated_type = 'string'
    help_text = 'A file URL as a string'

    def hydrate(self, bundle):
        """
        Create SimpleUploadedFile from data received from user.

        RFC 2397  for data url scheme is used:
            http://tools.ietf.org/html/rfc2397

        e.g.:
            data:image/png;base64,R0lGODlhEAAQAMQAAORHHOVSKudfOulrSOp3....

        :return: class:`SimpleUploadedFile` file created
        :raises:
            ValueError if content-type is not valid
            KeyError if format is not valid

        """

        value = super(Base64FileField, self).hydrate(bundle)
        if value:
            try:
                split_data = value.split(';')
                data = dict(re.split(':|,', item) for item in split_data)
                extension = mimetypes.guess_extension(
                    data.get('data', 'application/octet-stream'))
                value = SimpleUploadedFile(
                    'upload_image' + extension,
                    base64.b64decode(data['base64']),
                    data.get('data', 'application/octet-stream'))
            except (ValueError, KeyError):
                raise
        return value


class OptimizedToOneField(fields.ToOneField):

    """
    This modified field, allow to include resource_uri of related
    resources without doing another database query.

    This field is only useful when the resource URIs are built using
    the PK, /api/v1/model/<pk>/, if using slugs or any other fields,
    this optimization cannot be applied.

    Using select_related() in resource.meta.queryset also avoids
    doing extra queries for each object, can be used instead
    of this class.

    """

    def dehydrate(self, bundle, **kwargs):
        """
        If field is configured to only return the resource URI (full=False),
        a temporal object will be created with only the PK available,
        this key will be filled with the value saved at self.attribute_id

        In case, field's self.full is set to True, original dehydrate process
        will be used.

        """
        if not self.full:
            pk = getattr(bundle.obj, self.attribute + "_id", None)
            if not pk:
                if not self.null:
                    raise ApiFieldError(
                        """The model '%r' has an empty attribute '%s'
                        and doesn't allow a null value.""" %
                        (bundle.obj, self.attribute))
                return None
            # just create a temporal object with only PK
            temporal_obj = type('TemporalModel', (object,), {'pk': pk})()

            # from this point, is almost the same stuff that tastypie does.
            self.fk_resource = self.get_related_resource(temporal_obj)
            fk_bundle = Bundle(
                obj=temporal_obj, request=bundle.request)
            return self.dehydrate_related(fk_bundle, self.fk_resource)

        return super(OptimizedToOneField, self).dehydrate(bundle, **kwargs)


class CheckToManyField(fields.ToManyField):

    """
    Provides access to OneToManyField like in tastypie defaults but
    dehydration and any other process, will be done only if a
    permission check is passed.

        :param perms_check: function receiving a Bundle and validating
            the permissions, in case check return False, and empty
            list will be returned after dehydrated process

    """

    def __init__(self, *args, **kwargs):
        check = kwargs.pop('perms_check', None)
        super(CheckToManyField, self).__init__(*args, **kwargs)
        self.check = check

    def dehydrate(self, bundle, for_list=True):
        if self.check is not None:
            if not self.check(bundle):
                if not self.null:
                    raise ApiFieldError("The field '%s' does not pass \
                            permission check and does not support null" %
                                        (self.attribute))
                else:
                    return None
        result = super(CheckToManyField, self).dehydrate(bundle, for_list)
        # avoid returning [[]]
        if not result or not result[0]:
            return []
        return result

    def dehydrate_related(self, bundle, related_resource, for_list=True):
        if self.check is not None:
            if not self.check(bundle):
                if not self.null:
                    raise ApiFieldError("The field '%s' does not pass \
                            permission check and does not support null" %
                                        (self.attribute))
                else:
                    return None
        return super(CheckToManyField, self).dehydrate_related(
            bundle, related_resource, for_list)


class DateTimeField(fields.DateTimeField):

    """
    A datetime field that also handles '' dates as None
    """

    def convert(self, value):
        """
        Avoid parsing date if it is None

        """
        if not value:
            return None
        return super(DateTimeField, self).convert(value)
