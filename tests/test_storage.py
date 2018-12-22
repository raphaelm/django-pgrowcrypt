import pytest

from .testapp.models import Book


@pytest.mark.django_db
def test_save_cycle(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    b = Book.objects.with_key(key).first()
    assert b.title == 'The Lord of the Rings'
