from pgrowcrypt.models import EncryptedModel, EncryptedTextField


class Book(EncryptedModel):
    title = EncryptedTextField()

    def __str__(self):
        return self.title
