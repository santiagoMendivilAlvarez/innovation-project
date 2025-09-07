# Backend Django - Proyecto de Libros

Este es un proyecto Django que incluye un modelo completo para gestionar libros.

## Estructura del Proyecto

```
backend/
├── manage.py                 # Script de gestión de Django
├── db.sqlite3               # Base de datos SQLite
├── proyecto_backend/        # Configuración del proyecto
│   ├── __init__.py
│   ├── settings.py          # Configuración del proyecto
│   ├── urls.py             # URLs principales
│   ├── wsgi.py             # WSGI para producción
│   └── asgi.py             # ASGI para canales
└── libros/                  # Aplicación de libros
    ├── models.py           # Modelo Libro
    ├── admin.py            # Configuración del admin
    ├── views.py            # Vistas (por implementar)
    ├── urls.py             # URLs de la app (por implementar)
    └── migrations/         # Migraciones de la base de datos
```

## Modelo Libro

El modelo `Libro` incluye los siguientes campos:

- **titulo**: Título del libro (CharField, max 200 caracteres)
- **autor**: Autor del libro (CharField, max 100 caracteres)
- **isbn**: ISBN único del libro (CharField, max 13 caracteres, único)
- **descripcion**: Descripción del libro (TextField, opcional)
- **fecha_publicacion**: Fecha de publicación (DateField)
- **paginas**: Número de páginas (PositiveIntegerField)
- **precio**: Precio del libro (DecimalField)
- **calificacion**: Calificación de 0.0 a 5.0 (FloatField, opcional)
- **disponible**: Si el libro está disponible (BooleanField, default True)
- **fecha_creacion**: Fecha de creación del registro (DateTimeField, auto)
- **fecha_actualizacion**: Fecha de última actualización (DateTimeField, auto)

## Configuración

- **Idioma**: Español (es-es)
- **Zona horaria**: America/Mexico_City
- **Base de datos**: SQLite (por defecto)

## Comandos Útiles

### Ejecutar el servidor de desarrollo
```bash
python manage.py runserver
```

### Crear migraciones
```bash
python manage.py makemigrations
```

### Aplicar migraciones
```bash
python manage.py migrate
```

### Crear superusuario
```bash
python manage.py createsuperuser
```

### Acceder al panel de administración
1. Ejecutar el servidor: `python manage.py runserver`
2. Ir a: http://127.0.0.1:8000/admin/
3. Usuario: `admin`
4. Contraseña: `admin123`

## Próximos Pasos

- Implementar vistas y URLs para API REST
- Agregar serializers para Django REST Framework
- Implementar autenticación y permisos
- Agregar tests unitarios
- Configurar CORS para frontend
