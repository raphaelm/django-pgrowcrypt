from django.db.models import CASCADE, ForeignKey
from pgrowcrypt.models import EncryptedModel, EncryptedTextField


class Book(EncryptedModel):
    title = EncryptedTextField()
    author = ForeignKey('Author', null=True, on_delete=CASCADE)

    def __str__(self):
        return self.title


class Author(EncryptedModel):
    name = EncryptedTextField()

    def __str__(self):
        return self.name
