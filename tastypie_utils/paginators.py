# coding=utf-8

from tastypie.paginator import Paginator
from django.conf import settings


class InfinitePaginatorMixin(object):

    """
    Allow to send all the objects available (really, only 2000)
    Just use &limit=-1 at the request

    """

    def get_limit(self):
        """
        Returns 2000 when limit at GET params is set to -1

        """
        limit = int(self.request_data.get('limit', self.limit))

        if limit is None:
            return getattr(settings, 'API_LIMIT_PER_PAGE', 20)

        if limit == -1:
            return 2000
        elif self.max_limit and (limit > self.max_limit):
            return self.max_limit
        return limit


class NoTotalCountPaginator(Paginator):

    """
    Original paginator from tastypie but removing total_count query
    to improve perfomance

    """

    def get_count(self):
        """
            Just avoid calling count()
        """
        return -1

    def page(self):
        """
            total_count in meta isn't needed
        """
        output = super(NoTotalCountPaginator, self).page()
        del output['meta']['total_count']

        return output

