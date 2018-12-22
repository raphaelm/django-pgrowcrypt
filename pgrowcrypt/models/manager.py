from contextlib import contextmanager

from django.db import connections
from django.db.models import QuerySet


@contextmanager
def query_key(connection, key):
    connection._pgcolcrypt_key = key
    try:
        yield
    finally:
        del connection._pgcolcrypt_key


class EncryptedColumnsQuerySet(QuerySet):
    def __init__(self, *args, **kwargs):
        self.key = None
        super().__init__(*args, **kwargs)

    def with_key(self, key):
        self.key = key
        return self

    def _clone(self):
        c = super()._clone()
        c.key = self.key
        return c

    def __iter__(self):
        with query_key(connections[self.db], self.key):
            return super().__iter__()

    def _iterator(self, *args, **kwargs):
        with query_key(connections[self.db], self.key):
            return super()._iterator(*args, **kwargs)


EncryptedColumnsManager = EncryptedColumnsQuerySet.as_manager
