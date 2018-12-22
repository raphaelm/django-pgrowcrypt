Row-level encryption based on pgcrypto for Django
=================================================

**WARNING:** This is an experiment including some nasty ORM hacks and we do not yet recommend to use it in production.

.. image:: https://img.shields.io/pypi/v/django-pgcolcrypt.svg
   :target: https://pypi.python.org/pypi/django-pgcolcrypt

.. image:: https://travis-ci.com/raphaelm/django-pgcolcrypt.svg?branch=master
   :target: https://travis-ci.com/raphaelm/django-pgcolcrypt

.. image:: https://codecov.io/gh/raphaelm/django-pgcolcrypt/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/raphaelm/django-pgcolcrypt


This allows the encryption of values in specific columns using symmetric cryptography with the ``pgcrypto`` extension.
This is similar to `django-pgcrypto-expressions`_ and `django-pgcrypto-fields`_, but different in the regard that those
two encrypt all data with the *same* system-wide key and handle encryption fully transparently. In contrast, this library
allows to use *different* key per row/per query. A common use case would be to encrypt sensitive data with a key specific
to a user or to a client in a multi-tenant application.

Keep in mind that the actual encryption and decryption is performed in the database and the key is being sent to the database
in plain text, so this requires the connection to the database to be either local or encrypted and requires you to trust the
database administrator.

Further limitations:

* Works only on PostgreSQL (obviously)

Usage
-----

You will need to use both a custom model base class and a custom field class::

    from pgrowcrypt.models import EncryptedModel, EncryptedTextField


    class Book(EncryptedModel):
        title = EncryptedTextField()

        def __str__(self):
            return self.title


    from django.db import models
    from jsonfallback.fields import FallbackJSONField


Then, you can work with the model like this:

    >>> b = Book(title='Harry Potter', _key='pgLWLYqQb4zR9K1Im3GUsLXaILnU7q')
    >>> b.save()
    >>> Book.objects.with_key('pgLWLYqQb4zR9K1Im3GUsLXaILnU7q').all()
    <QuerySet[<Book: Harry Potter>]>

License
-------
The code in this repository is published under the terms of the Apache License. 
See the LICENSE file for the complete license text.

This project is maintained by Raphael Michel <mail@raphaelmichel.de>. See the
AUTHORS file for a list of all the awesome folks who contributed to this project.

.. _django-pgcrypto-expressions: https://github.com/orcasgit/django-pgcrypto-expressions
.. _django-pgcrypto-fields: https://github.com/incuna/django-pgcrypto-fields