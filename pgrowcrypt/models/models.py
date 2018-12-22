from contextlib import contextmanager

from django.db import connections, models

from .fields import EncryptedField, EncryptionValueWrapper
from .manager import EncryptedColumnsManager, query_key


class EncryptedModel(models.Model):
    objects = EncryptedColumnsManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        self.__key = kwargs.pop('_key', None)
        super().__init__(*args, **kwargs)

    @classmethod
    def from_db(cls, db, field_names, values):
        v = super().from_db(db, field_names, values)
        if hasattr(connections[db], '_pgcolcrypt_key'):
            v.__key = connections[db]._pgcolcrypt_key
        return v

    def refresh_from_db(self, using=None, fields=None):
        with query_key(connections[using or self._state.db], self.__key):
            super().refresh_from_db(using, fields)

    @contextmanager
    def __wrap_values(self):
        fieldnames = []
        for f in self._meta.get_fields():
            if isinstance(f, EncryptedField):
                if not self.__key:
                    raise TypeError("No key set to encrypt the value in column '{}'.".format(f.name))
                setattr(self, f.name, EncryptionValueWrapper(getattr(self, f.name), self.__key))
                fieldnames.append(f.name)

        try:
            yield
        finally:
            for k in fieldnames:
                setattr(self, k, getattr(self, k).value)

    def save(self, *args, **kwargs):
        if '_key' in kwargs:
            self.__key = kwargs.pop('_key')

        with self.__wrap_values():
            super().save(*args, **kwargs)
