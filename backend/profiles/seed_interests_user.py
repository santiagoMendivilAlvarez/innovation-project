"""
Seed for generating random interests for users.
"""
# pylint: disable=E1101
import random
from faker import Faker
from profiles.models import InteresUsuario
from authentication.models import CustomUser
from libros.models import Categoria


faker = Faker('es_MX')

def run():
    users = list(CustomUser.objects.all())
    categorias = list(Categoria.objects.all())

    for user in users:
        for _ in range(3):
            InteresUsuario.objects.create(
                usuario = user, 
                categoria = random.choice(categorias),
                nivel_interes = random.randint(1, 10),
                fecha_creacion = faker.date_time_this_year(),
                fecha_actualizacion = faker.date_time_this_year()
            )

run()
