from django.contrib import admin
from .models import Genre, FilmWork, PersonFilmWork
# Register your models here.


class PersonRoleInline(admin.TabularInline):
    model = PersonFilmWork
    extra = 0


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating')
    fields = (
        'title', 'type', 'description', 'creation_date', 'certificate',
        'file_path', 'rating',
    )
    inlines = [
        PersonRoleInline
    ]
