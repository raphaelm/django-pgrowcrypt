import pytest

from .testapp.models import Book


@pytest.mark.django_db
def test_save_and_retrieve_cycles(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    b = Book.objects.with_key(key).first()
    assert b.title == 'The Lord of the Rings'
    b.title = 'Harry Potter'
    b.save()
    b = Book.objects.with_key(key).first()
    assert b.title == 'Harry Potter'
