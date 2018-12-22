from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.expressions import Col, Expression, Func, Value
from django.utils.functional import cached_property


class EncryptionValueWrapper(Func):

    def __init__(self, value, key, **extra):
        self.value = value
        self.key = key
        if not isinstance(value, Expression):
            value = Value(value)
        super().__init__(value, **extra)

    def __str__(self):
        return self.value

    def __repr__(self):
        return "EncryptionValueWrapper(%r, key)" % self.value

    def as_sql(self, compiler, connection):
        sql_parts = []
        params = []
        for arg in self.source_expressions:
            arg_sql, arg_params = compiler.compile(arg)
            sql_parts.append(arg_sql)
            params.extend(arg_params)

        params.append(self.key)
        return "pgp_sym_encrypt({}::text, %s)".format(', '.join(sql_parts)), params


class EncryptedField(models.Field):

    def __init__(self, *args, **kwargs):
        for k in ('primary_key', 'unique', 'db_index'):
            if kwargs.get('primary_key'):
                raise ImproperlyConfigured(
                    "CryptedTextField does not support {}.".format(k)
                )

        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'bytea'

    def _get_base_db_type(self, connection):
        return super().db_type(connection)

    def get_db_prep_save(self, value, connection):
        return value

    def get_col(self, alias, output_field=None):
        if output_field is None:
            output_field = self
        if alias != self.model._meta.db_table or output_field != self:
            return DecryptedCol(alias, self, output_field)
        else:
            return self.cached_col

    @cached_property
    def cached_col(self):
        return DecryptedCol(
            self.model._meta.db_table,
            self,
        )

    def check(self, **kwargs):
        errors = super().check(**kwargs)
        errors.extend(self._check_model_class())
        return errors

    def _check_model_class(self):
        from .models import EncryptedModel

        errors = []
        if not issubclass(self.model, EncryptedModel):
            errors.append(
                checks.Error(
                    'Do not use EncryptedField types on a model that does not inherit from EncryptedModel.',
                    id='pgrowcrypt.E001',
                ),
            )
        if '_key' in self.model._meta.fields:
            errors.append(
                checks.Error(
                    'EncryptedModel subclasses should not have a field called "_key".',
                    id='pgrowcrypt.E002',
                ),
            )
        return errors


class DecryptedCol(Col):
    decrypt_sql_template = "pgp_sym_decrypt({sql}, %s)::{dbtype}"

    def __init__(self, alias, target, output_field=None):
        self.target = target
        super(DecryptedCol, self).__init__(alias, target, output_field)

    def as_sql(self, compiler, connection):
        sql, params = super(DecryptedCol, self).as_sql(compiler, connection)
        decrypt_sql = self.decrypt_sql_template.format(
            dbtype=self.target._get_base_db_type(connection),
            sql=sql
        )
        params = list(params)
        params.append(getattr(connection, '_pgrowcrypt_key', '') or ' ')
        return decrypt_sql, tuple(params)


class EncryptedTextField(EncryptedField, models.TextField):
    pass
