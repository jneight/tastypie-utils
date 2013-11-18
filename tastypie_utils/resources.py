# coding=utf-8

from django.core.exceptions import ObjectDoesNotExist


class GetMultipleResourceMixin(object):

    """
    When doing a GET with multiple ids (/1;2;3;4/), tastypie does one database
    query for each id, this mixin will retrieve all objects in only one query,
    in case of any error, will fallback to original behaviour

    """

    def get_multiple(self, request, **kwargs):
        """
        Method called by dispatch() when a list of ids is used

        :return: HTTP response ready to be sent to user

        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Rip apart the list then iterate.
        detail_uri_name = self._meta.detail_uri_name
        collection_name = self._meta.collection_name
        kwarg_name = '%s_list' % detail_uri_name

        # build the list of ids to query
        obj_identifiers = kwargs.get(kwarg_name, '').split(';')
        obj_identifiers = set(obj_identifiers)

        base_bundle = self.build_bundle(request=request)

        try:
            # build the query to filter with all the ids
            objects = self.obj_get_multiple(
                bundle=base_bundle,
                **{'%s__in' % detail_uri_name: obj_identifiers})
            # build the bundle for each object
            bundles = [
                self.build_bundle(obj=obj, request=request)
                for obj in objects]
            objects = [self.full_dehydrate(bundle) for bundle in bundles]
            # objects not found are also returned
            found = [
                str(self.get_bundle_detail_data(bundle))
                for bundle in bundles]
            not_found = list(set(obj_identifiers) - set(found))
        except NotImplementedError:
            # fallback
            objects = []
            not_found = []
            for identifier in obj_identifiers:
                try:
                    obj = self.obj_get(
                        request,
                        **{self._meta.detail_uri_name: identifier})
                    bundle = self.build_bundle(obj=obj, request=request)
                    bundle = self.full_dehydrate(bundle)
                    objects.append(bundle)
                except ObjectDoesNotExist:
                    not_found.append(identifier)

        object_list = {
            collection_name: objects,
        }

        if len(not_found):
            object_list['not_found'] = not_found

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def obj_get_multiple(self, bundle, **kwargs):
        """
        A ORM-specific implementation of ``obj_get_multiple``.

        :param bundle: bundle with request, used for authorizations
        :param kwargs: All the filters going to be applied

        :return: queryset
        :raises: BadRequest in case any filter is invalid
        """

        filters = kwargs
        try:
            base_object_list = self.apply_filters(bundle.request, filters)
            return self.authorized_read_list(base_object_list, bundle)
        except ValueError:
            raise BadRequest("Invalid resource lookup data provided"
                             " (mismatched type).")

