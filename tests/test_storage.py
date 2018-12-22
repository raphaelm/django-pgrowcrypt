import pytest
from django.db import InternalError

from .testapp.models import Author, Book


@pytest.mark.django_db
def test_save_and_retrieve_cycles(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    b = Book.objects.with_key(key).first()
    assert b.title == 'The Lord of the Rings'
    b.title = 'Harry Potter'
    b.save()
    b = Book.objects.with_key(key).first()
    assert b.title == 'Harry Potter'


@pytest.mark.django_db
def test_create_from_query(key):
    Book.objects.with_key(key).create(title='The Lord of the Rings')
    b = Book.objects.with_key(key).first()
    assert b.title == 'The Lord of the Rings'


@pytest.mark.django_db
def test_delete(key):
    b = Book.objects.with_key(key).create(title='The Lord of the Rings')
    b.delete()
    assert Book.objects.with_key(key).count() == 0


@pytest.mark.django_db
def test_refresh_from_db(key):
    b = Book.objects.with_key(key).create(title='The Lord of the Rings')
    b.refresh_from_db()
    assert b.title == 'The Lord of the Rings'


@pytest.mark.django_db
def test_missing_key():
    with pytest.raises(TypeError):
        Book.objects.create(title='The Lord of the Rings')
    Book.objects.create(title='The Lord of the Rings', _key='a')
    with pytest.raises(InternalError):
        Book.objects.first()


@pytest.mark.django_db
def test_bulk_create(key):
    bulk = [
        Book(title='The Lord of the Rings', _key=key),
        Book(title='Harry Potter', _key=key)
    ]
    Book.objects.bulk_create(bulk)
    assert Book.objects.with_key(key).filter(title__icontains='Rings').count() == 1
    assert Book.objects.with_key(key).filter(title__icontains='Potter').count() == 1


@pytest.mark.django_db
def test_store_prefetched(key, django_assert_num_queries):
    b1 = Book.objects.create(title='Harry Potter', author=Author.objects.create(name='J. K. Rowling', _key=key), _key=key)
    authors = list(Author.objects.with_key(key).prefetch_related('book_set').order_by('name'))
    b1 = authors[0].book_set.all()[0]
    b1.title = 'Harry Potter 2'
    b1.save()
