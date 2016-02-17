# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from bson.objectid import ObjectId

from udata.utils import Paginable


log = logging.getLogger(__name__)


class SearchResult(Paginable):
    '''An ElasticSearch result wrapper for easy property access'''
    def __init__(self, query, result):
        self.result = result
        self.query = query
        self._objects = None

    @property
    def total(self):
        return self.result.get('hits', {}).get('total', 0)

    @property
    def max_score(self):
        return self.result.get('hits', {}).get('max_score', 0)

    @property
    def page(self):
        return (self.query.page or 1) if self.pages else 1

    @property
    def page_size(self):
        return self.query.page_size

    @property
    def class_name(self):
        return self.query.adapter.model.__name__

    def get_ids(self):
        return [hit['_id']
                for hit in self.result.get('hits', {}).get('hits', [])]

    def get_objects(self):
        if not self._objects:
            ids = [ObjectId(id) for id in self.get_ids()]
            objects = self.query.adapter.model.objects.in_bulk(ids)
            self._objects = [objects.get(id) for id in ids]
        return self._objects

    @property
    def objects(self):
        return self.get_objects()

    @property
    def facets(self):
        return dict(
            (f, self.get_facet(f)) for f in self.query.facets_kwargs
        )

    def __iter__(self):
        for obj in self.get_objects():
            yield obj

    def __len__(self):
        return len(self.result.get('hits', {}).get('hits', []))

    def __getitem__(self, index):
        return self.get_objects()[index]

    def get_facet(self, name):
        if name not in self.query.adapter.facets:
            return None
        return self.query.adapter.facets[name].from_response(name, self.result)

    def get_range(self, name):
        min_name = '{0}_min'.format(name)
        max_name = '{0}_max'.format(name)
        if name not in self.query.adapter.filters:
            return None
        aggs = self.result.get('aggregations', {})
        if not aggs or min_name not in aggs or max_name not in aggs:
            return None
        spec = self.query.adapter.filters[name]
        min_value = aggs[min_name]['value'] or 0
        max_value = aggs[max_name]['value'] or 0
        return {
            'min': spec.cast(min_value),
            'max': spec.cast(max_value),
            'query_min': 0,
            'query_max': 0,
        }

    def label_func(self, name):
        if name not in self.query.adapter.facets:
            return None
        return self.query.adapter.facets[name].labelize

    def labelize(self, name, value):
        func = self.label_func(name)
        return func(value) if func else value


class SearchIterator(object):
    """An ElasticSearch scroll result iterator

    that fetch objects on each hit.
    """
    def __init__(self, query, result):
        self.result = result or self._empty()
        self.query = query

    def _empty(self):
        return (x for x in list())

    def __iter__(self):
        for hit in self.result:
            yield self.query.adapter.model.objects.get(id=hit['_id'])
