import pytest
from django.db.models import F, Max, Value
from django.db.models.functions import Concat, Lower

from .testapp.models import Author, Book


@pytest.mark.django_db
def test_query_filter_by_encrypted_values(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).filter(title='The Lord of the Rings').count() == 1
    assert Book.objects.with_key(key).filter(title='Harry Potter').count() == 0


@pytest.mark.django_db
def test_query_annotate_by_encrypted_values(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert list(Book.objects.with_key(key).annotate(k=Lower('title')).values_list('k', flat=True)) == [
        'the lord of the rings'
    ]


@pytest.mark.django_db
def test_queryset_count(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).filter(title__icontains='Rings').count() == 1
    assert len(Book.objects.with_key(key).filter()) == 1


@pytest.mark.django_db
def test_queryset_exists(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert bool(Book.objects.with_key(key).filter(title__icontains='Rings'))
    assert Book.objects.with_key(key).filter(title__icontains='Lord').exists()


@pytest.mark.django_db
def test_queryset_aggregate(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).aggregate(m=Max('title')) == {
        'm': 'The Lord of the Rings'
    }


@pytest.mark.django_db
def test_queryset_get(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).get().title == 'The Lord of the Rings'


@pytest.mark.django_db
def test_queryset_boundaries(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).earliest('pk').title == 'The Lord of the Rings'
    assert Book.objects.with_key(key).latest('pk').title == 'The Lord of the Rings'
    assert Book.objects.with_key(key).first().title == 'The Lord of the Rings'
    assert Book.objects.with_key(key).last().title == 'The Lord of the Rings'


@pytest.mark.django_db
def test_queryset_iterators(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    assert len(list(Book.objects.with_key(key).iterator())) == 1
    assert len(list(Book.objects.with_key(key).values('title').iterator())) == 1
    assert len(list(Book.objects.with_key(key).values_list('title').iterator())) == 1
    assert len(list(Book.objects.with_key(key).values_list('title', flat=True).iterator())) == 1


@pytest.mark.django_db
def test_queryset_in_bulk(key):
    b = Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).in_bulk([b.pk]) == {
        b.pk: b
    }


@pytest.mark.django_db
def test_queryset_update(key):
    b = Book.objects.create(title='The Lord of the Rings', _key=key)
    Book.objects.with_key(key).update(title='Harry Potter')
    b = Book.objects.with_key(key).get(pk=b.pk)
    assert b.title == 'Harry Potter'


@pytest.mark.django_db
def test_queryset_update_expression(key):
    b = Book.objects.create(title='The Lord of the Rings', _key=key)
    Book.objects.with_key(key).filter(title='The Lord of the Rings').update(title=Concat(F('title'), Value('!')))
    b = Book.objects.with_key(key).get(pk=b.pk)
    assert b.title == 'The Lord of the Rings!'


@pytest.mark.django_db
def test_queryset_delete_filter(key):
    Book.objects.create(title='The Lord of the Rings', _key=key)
    Book.objects.with_key(key).filter(title='The Lord of the Rings').delete()
    assert Book.objects.with_key(key).count() == 0


@pytest.mark.django_db
def test_queryset_get_or_create(key):
    b = Book.objects.create(title='The Lord of the Rings', _key=key)
    assert Book.objects.with_key(key).get_or_create(title='The Lord of the Rings') == (b, False)
    assert Book.objects.with_key(key).get_or_create(title='Harry Potter')[1]
    Book.objects.with_key(key).get(title='Harry Potter')


@pytest.mark.django_db
def test_queryset_update_or_create(key):
    b = Book.objects.create(title='The Lord of the Rings', _key=key)
    Book.objects.with_key(key).update_or_create(pk=b.pk, defaults={'title': 'Harry Potter'})
    Book.objects.with_key(key).get(title='Harry Potter')
    Book.objects.with_key(key).update_or_create(pk=b.pk + 1, defaults={'title': 'Marry Poppins'})
    Book.objects.with_key(key).get(title='Marry Poppins')


@pytest.mark.django_db
def test_queryset_select_related(key, django_assert_num_queries):
    a = Author.objects.create(name='J. R. R. Tolkien', _key=key)
    b = Book.objects.create(title='The Lord of the Rings', author=a, _key=key)
    with django_assert_num_queries(1):
        b = Book.objects.with_key(key).select_related('author').first()
    assert b.author == a


@pytest.mark.django_db
def test_queryset_prefetch_related(key, django_assert_num_queries):
    b1 = Book.objects.create(title='Harry Potter', author=Author.objects.create(name='J. K. Rowling', _key=key), _key=key)
    b2 = Book.objects.create(title='The Lord of the Rings', author=Author.objects.create(name='J. R. R. Tolkien', _key=key), _key=key)
    with django_assert_num_queries(2):
        authors = list(Author.objects.with_key(key).prefetch_related('book_set').order_by('name'))
        assert list(authors[0].book_set.all()) == [b1]
        assert list(authors[1].book_set.all()) == [b2]
