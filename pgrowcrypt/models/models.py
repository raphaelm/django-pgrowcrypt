from django.db import models

from .fields import EncryptedField, EncryptionValueWrapper
from .manager import EncryptedColumnsManager


class EncryptedModel(models.Model):
    objects = EncryptedColumnsManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        if '_key' in kwargs:
            self.__key = kwargs.pop('_key')
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if '_key' in kwargs:
            self.__key = kwargs.pop('_key')

        fieldnames = []
        for f in self._meta.get_fields():
            if isinstance(f, EncryptedField):
                setattr(self, f.name, EncryptionValueWrapper(getattr(self, f.name), self.__key))
                fieldnames.append(f.name)
        super().save(*args, **kwargs)
        for k in fieldnames:
            setattr(self, k, getattr(self, k).value)
