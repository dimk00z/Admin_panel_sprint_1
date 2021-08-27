from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class TimeStampedMixin:
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FilmworkType(models.TextChoices):
    MOVIE = 'movie', _('movie')
    TV_SHOW = 'tv_show', _('TV Show')


class Genre(TimeStampedMixin, models.Model):
    id = models.UUIDField(
        primary_key=True)
    name = models.CharField(
        _('title'),
        max_length=100)
    description = models.TextField(
        _('description'), blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'content.genre'


class FilmWork(TimeStampedMixin, models.Model):
    id = models.UUIDField(
        primary_key=True)

    title = models.CharField(
        _('title'), max_length=250)
    description = models.TextField(
        _('description'), blank=True, null=True)
    creation_date = models.DateField(
        _('creation date'), blank=True, null=True)
    certificate = models.TextField(
        _('certificate'), blank=True, null=True)
    file_path = models.TextField(
        _('file'), upload_to='film_works/',
        blank=True, null=True)
    rating = models.DecimalField(
        _('rating'), validators=[MinValueValidator(0)], blank=True)
    type = models.CharField(
        _('type'), max_length=20,
        choices=FilmworkType.choices)
    genres = models.ManyToManyField(Genre, through='FilmworkGenre')

    class Meta:
        # managed = False
        db_table = 'content.film_work'


class GenreFilmWork(models.Model):
    id = models.UUIDField(
        primary_key=True)
    film_work = models.ForeignKey(FilmWork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # managed = False
        db_table = 'content.genre_film_work'
        unique_together = (('film_work', 'genre'))


class Person(TimeStampedMixin, models.Model):
    id = models.UUIDField(primary_key=True)
    full_name = models.CharField(
        _('full_name'), max_length=200)
    birth_date = models.DateField(
        _('birth_date'), blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'content.person'


class PersonFilmWork(models.Model):
    id = models.UUIDField(primary_key=True)
    role = models.CharField(
        _('role'), max_length=50, blank=True, null=True)
    film_work = models.ForeignKey(FilmWork, models.DO_NOTHING)
    person_id = models.UUIDField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        # managed = False
        db_table = 'content.person_film_work'
        unique_together = (('film_work', 'person_id', 'role'),)
