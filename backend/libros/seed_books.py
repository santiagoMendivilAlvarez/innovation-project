"""
Seed for generating N number of random books
"""
# pylint: disable=E1101
import random
from decimal       import Decimal
from faker         import Faker
from libros.models import Categoria, Libro


faker = Faker('es_MX')


def run():
    """
    Run function to call the random books
    """
    categories = list(Categoria.objects.all())
    books_quan = 100
    for _ in range(books_quan):
        category = random.choice(categories)
        title = faker.sentence(nb_words=4)
        author = faker.name()
        isbn = faker.unique.isbn13()
        image_url = faker.image_url(width=200, height=300)
        description = faker.paragraph(nb_sentences=5)
        publish_date = faker.date_between(start_date='-10y', end_date='today')
        pages = random.randint(100, 1000)
        price = round(random.uniform(100, 800), 2)
        calification = round(random.uniform(0, 5), 1)
        available = random.choice([True, True, True, False])
        print(f"Creating book: {title} by {author}")
        Libro.objects.create(
            categoria=category,
            titulo=title,
            autor=author,
            isbn=isbn,
            imagen_url=image_url,
            descripcion=description,
            fecha_publicacion=publish_date,
            paginas=pages,
            precio=Decimal(price),
            calificacion=calification,
            disponible=available
        )
    print(f"Successfully created {books_quan} books.")

run()