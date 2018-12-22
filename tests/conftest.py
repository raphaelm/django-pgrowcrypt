import os

import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

import django

django.setup()


@pytest.fixture(params=[
    "BQXhsXpgjbsa8Yj8r4ttrSciXLMJxJ",
    "rosenkohl",
    "key'with'single'quotes",
    'key"with"double"quotes',
    "key`with`backticks",
    "SELECT key_with_keywords()",
    "key:with:parameters:%s:%s"
])
def key(request):
    return request.param