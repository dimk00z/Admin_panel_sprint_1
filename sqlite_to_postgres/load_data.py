import logging
from json import loads
from utils.dataclasses import FilmWork, Person, Genre, FilmWorkPerson, FilmWorkGenre
from utils.env_load import load_params

from typing import List

import sqlite3

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

logger = logging.getLogger(__file__)


class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.cursor = connection.cursor()
        self.sqlite_data = {}

    def _get_tables_names(self) -> List[str]:
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        return [table_name[0] for table_name in self.cursor.fetchall(
        ) if table_name[0] != 'sqlite_sequence']

    def _load_all_data(self) -> None:
        for table_name in self._get_tables_names():
            current_table = []
            self.cursor.execute(f'SELECT * FROM {table_name}')
            column_names = tuple(map(lambda x: x[0], self.cursor.description))
            current_table.append(column_names)
            for row in self.cursor.fetchall():
                current_table.append(row)
            self.sqlite_data[table_name] = current_table

    def _get_person(self, name, persons: dict) -> Person:
        if name in persons:
            return persons[name]
        person = Person(full_name=name)
        persons[name] = person
        return person

    def _add_persons(self, table_name: str, typed_persons: dict, persons: dict) -> None:
        for person_old_id, name in self.sqlite_data[table_name][1:]:
            person = Person(full_name=name)
            typed_persons[person_old_id] = person
            persons[name] = person

    def _sanitize_data(self):
        sanitized_data = {
            'film_work': [],
            'genre': [],
            'person': [],
            'genre_film_work': [],
            'person_film_work': [],
        }
        genres = {}
        persons = {}

        actors = {}
        writers = {}
        self._add_persons(table_name='actors',
                          typed_persons=actors,
                          persons=persons)
        self._add_persons(table_name='writers',
                          typed_persons=writers,
                          persons=persons)

        films_with_actors = {}
        for film_old_id, actor_old_id in self.sqlite_data['movie_actors'][1:]:
            if film_old_id not in films_with_actors:
                films_with_actors[film_old_id] = set()
            films_with_actors[film_old_id].add(actor_old_id)

        for row in self.sqlite_data['movies'][1:]:
            film_old_id = row[0]
            film_work = FilmWork(
                title=row[4],
                description=row[5],
                rating=row[7]
            )
            sanitized_data['film_work'].append(
                film_work
            )
            for genre_name in row[1].split(','):
                genre_name = genre_name.strip()
                if genre_name not in genres:
                    genre = Genre(name=genre_name)
                    genres[genre_name] = genre
                    sanitized_data['genre'].append(
                        Genre(name=genre))
                else:
                    genre = genres[genre_name]
                sanitized_data['genre_film_work'].append(
                    FilmWorkGenre(
                        id_film=film_work.id,
                        id_genre=genre.id
                    )
                )
            persons_for_movie = []
            if row[3]:
                persons_for_movie.append(
                    writers[row[3]]
                )
            if row[-1]:
                for writer_id_info in loads(row[-1]):
                    writer_old_id = tuple(writer_id_info.values())[0]
                    writer = writers[writer_old_id]
                    persons_for_movie.append(writer)
            for director_name in row[2].split(','):
                director_name = director_name.strip()
                director = self._get_person(director_name.strip(), persons)
                persons_for_movie.append(director)
            for actor_old_id in films_with_actors[film_old_id]:
                persons_for_movie.append(
                    actors[int(actor_old_id)]
                )
            for person in persons_for_movie:
                sanitized_data['person_film_work'].append(
                    FilmWorkPerson(
                        id_film=film_work.id,
                        id_person=person.id
                    ))

        sanitized_data['person'] = [
            person for _, person in persons.items()
        ]
        return sanitized_data
        # print(len(sanitized_data['person_film_work']))

    def load_movies(self) -> bool:
        self._load_all_data()
        self._sanitize_data()


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    # postgres_saver = PostgresSaver(pg_conn)
    sqlite_loader = SQLiteLoader(connection)
    data = sqlite_loader.load_movies()
    # postgres_saver.save_all_data(data)


def main():
    # try:
    logging.basicConfig(level=logging.DEBUG)
    script_params = load_params(
        required_params=[
            "dbname",
            "user",
            "password",
            "host",
            "port",
            "db_sqlite_file",
        ])
    logger.info(script_params)
    dsl = {'dbname': script_params['dbname'],
           'user': script_params['user'],
           'password': script_params['password'],
           'host': script_params['host'],
           'port': script_params['port'],
           'options': '-c search_path=content'}
    with sqlite3.connect('db.sqlite') as sqlite_conn:
        with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
            load_from_sqlite(sqlite_conn, pg_conn)


# except Exception as ex:
#     print(ex)


if __name__ == '__main__':
    main()
