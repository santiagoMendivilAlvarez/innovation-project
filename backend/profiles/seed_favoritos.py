# pylint: disable=E1101
import random
from faker                 import Faker
from profiles.models       import Favorito
from authentication.models import CustomUser
from libros.models         import Libro


faker = Faker('es_MX')


def run():
    users = list(CustomUser.objects.all())
    libros = list(Libro.objects.all())

    for user in users:
        for _ in range(10):
            Favorito.objects.create(
                usuario = user,
                libro = random.choice(libros),
                fecha_favorito = faker.date_time_this_year()
            )
run()