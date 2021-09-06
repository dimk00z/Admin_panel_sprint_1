from django.contrib import admin
from .models import Genre, Person, FilmWork


class PersonInLineAdmin(admin.TabularInline):
    model = FilmWork.persons.through
    extra = 0


class GenreInLineAdmin(admin.TabularInline):
    model = FilmWork.genres.through
    extra = 0


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date')
    fields = ('full_name', 'birth_date')
    inlines = (PersonInLineAdmin,)
    search_fields = ('full_name', 'birth_date')


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating')
    fields = (
        'title', 'type', 'description', 'creation_date', 'certificate',
        'file_path', 'rating',
    )
    raw_id_fields = ('genres', 'persons')
    inlines = [
        PersonInLineAdmin,
        GenreInLineAdmin,
    ]
    search_fields = ('title', 'description', 'type', 'genres')
