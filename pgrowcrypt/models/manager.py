from contextlib import ExitStack, contextmanager

from django.db import connections
from django.db.models import QuerySet

from .fields import EncryptedField, EncryptionValueWrapper


@contextmanager
def query_key(connection, key):
    if getattr(connection, '_pgcolcrypt_key', None):
        # be re-entry safe (required for prefetch_related)
        yield
        return
    connection._pgcolcrypt_key = key
    try:
        yield
    finally:
        del connection._pgcolcrypt_key


class EncryptedColumnsQuerySet(QuerySet):
    def __init__(self, *args, **kwargs):
        self.key = None
        super().__init__(*args, **kwargs)

    def wrap_method(method):
        def wrapped_method(self, *args, **kwargs):
            with query_key(connections[self.db], self.key):
                return getattr(super(), method)(*args, **kwargs)

        return wrapped_method

    def _iterator(self, use_chunked_fetch, chunk_size):
        with query_key(connections[self.db], self.key):
            yield from super()._iterator(use_chunked_fetch, chunk_size)

    _fetch_all = wrap_method('_fetch_all')
    count = wrap_method('count')
    exists = wrap_method('exists')
    aggregate = wrap_method('aggregate')
    delete = wrap_method('delete')
    _prefetch_related_objects = wrap_method('_prefetch_related_objects')

    def bulk_create(self, objs, batch_size=None):
        with ExitStack() as stack:
            for obj in objs:
                stack.enter_context(obj._EncryptedModel__wrap_values())
            return super().bulk_create(objs, batch_size)

    def create(self, **kwargs):
        if self.key:
            kwargs['_key'] = self.key
        return super().create(**kwargs)

    def update(self, **kwargs):
        for f in self.model._meta.get_fields():
            if isinstance(f, EncryptedField):
                if f.name in kwargs:
                    kwargs[f.name] = EncryptionValueWrapper(kwargs[f.name], self.key)
        with query_key(connections[self.db], self.key):
            return super().update(**kwargs)

    def _create_object_from_params(self, lookup, params, lock=False):
        if self.key:
            params['_key'] = self.key
        return super()._create_object_from_params(lookup, params, lock)

    def with_key(self, key):
        self.key = key
        return self

    def _clone(self):
        c = super()._clone()
        c.key = self.key
        return c


EncryptedColumnsManager = EncryptedColumnsQuerySet.as_manager
