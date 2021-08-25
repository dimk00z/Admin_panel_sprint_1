import os
import logging

from json import loads

from utils.dataclasses import FilmWork, Person, Genre, FilmWorkPerson, FilmWorkGenre
from utils.list_utils import group_elements
from utils.env_load import load_params

from typing import List

import sqlite3

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.DEBUG)


class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.cursor: connection.cursor = connection.cursor()
        self.sqlite_data: dict = {}

    def _get_all_tables_names(self) -> List[str]:
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';")
        return [table_name[0] for table_name in self.cursor.fetchall(
        ) if table_name[0] != 'sqlite_sequence']

    def _load_all_sqlite_data(self) -> None:
        for table_name in self._get_all_tables_names():
            current_table: list = []
            self.cursor.execute(f'SELECT * FROM {table_name}')
            column_names = tuple(map(lambda x: x[0], self.cursor.description))
            current_table.append(column_names)
            for row in self.cursor.fetchall():
                current_table.append(row)
            self.sqlite_data[table_name] = current_table

    def _get_or_create_person(self, name: str, persons: dict) -> Person:
        if name in persons:
            return persons[name]
        person: Person = Person(full_name=name)
        persons[name] = person
        return person

    def _add_persons(self, table_name: str,
                     typed_persons: dict,
                     persons: dict) -> None:
        for person_old_id, name in self.sqlite_data[table_name][1:]:
            person: Person = Person(full_name=name)
            typed_persons[person_old_id] = person
            persons[name] = person

    def _sanitize_data(self) -> dict:
        sanitized_data: dict = {
            'film_work': [],
            'genre': [],
            'person': [],
            'genre_film_work': [],
            'person_film_work': [],
        }
        persons: dict = {}
        genres: dict = {}
        actors: dict = {}
        writers: dict = {}
        self._add_persons(table_name='actors',
                          typed_persons=actors,
                          persons=persons)
        self._add_persons(table_name='writers',
                          typed_persons=writers,
                          persons=persons)

        films_with_actors: dict = {}
        for film_old_id, actor_old_id in self.sqlite_data['movie_actors'][1:]:
            if film_old_id not in films_with_actors:
                films_with_actors[film_old_id] = set()
            films_with_actors[film_old_id].add(actor_old_id)

        for row in self.sqlite_data['movies'][1:]:
            film_old_id: str = row[0]
            film_work: FilmWork = FilmWork(
                title=row[4],
                description=row[5],
                rating=row[7] if row[7] != 'N/A' else 0.0
            )
            sanitized_data['film_work'].append(
                film_work
            )
            for genre_name in row[1].split(','):
                genre_name: str = genre_name.strip()
                if genre_name not in genres:
                    genre: Genre = Genre(name=genre_name)
                    genres[genre_name]: Genre = genre
                    sanitized_data['genre'].append(
                        Genre(name=genre_name))
                else:
                    genre: Genre = genres[genre_name]
                sanitized_data['genre_film_work'].append(
                    FilmWorkGenre(
                        id_film=film_work.id,
                        id_genre=genre.id
                    )
                )
            persons_for_movie: list = []
            if row[3]:
                persons_for_movie.append(
                    writers[row[3]]
                )
            if row[-1]:
                for writer_id_info in loads(row[-1]):
                    writer_old_id: str = tuple(writer_id_info.values())[0]
                    writer: Person = writers[writer_old_id]
                    persons_for_movie.append(writer)
            for director_name in row[2].split(','):
                director_name: str = director_name.strip()
                director: Person = self._get_or_create_person(
                    director_name.strip(),
                    persons)
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
            person for person in persons.values()
        ]
        return sanitized_data

    def load_movies(self) -> dict:
        self._load_all_sqlite_data()
        data = self._sanitize_data()
        logger.info('Data loaded from sqlite db')
        return data


class PostgresSaver:
    def __init__(self, pg_conn: _connection):
        self.cursor = pg_conn.cursor()

    def _save_data_to_table(self, table_name: str,
                            rows: list,
                            schema: str = 'content',
                            max_operations: int = 500):
        rows_names: str = ', '.join(rows[0])
        grouped_rows = group_elements(rows[1:], max_operations)
        for page_number, rows in enumerate(grouped_rows):
            sql_template = f"INSERT INTO {schema}.{table_name} ({rows_names})\nVALUES "
            data_str = ', \n'.join(map(lambda y: f"({y})",
                                       [','.join(map(lambda x: "'{}'".format(x.replace("'", "''")), map(str, row)))
                                        for row in rows
                                        ])
                                   )

            excluded_str = ', '.join([f'{name}=EXCLUDED.{name}' for name in rows[0]])
            # on_conflict_str = f'ON CONFLICT (id) DO UPDATE SET {excluded_str};'
            on_conflict_str = 'ON CONFLICT (id) DO NOTHING;'
            sql_template = '\n'.join((sql_template, data_str, on_conflict_str))
            self.cursor.execute(sql_template)
            rows_count = len(rows)
            logger.info(f'Loaded page #{page_number}:{rows_count} rows for table:{table_name}')

    def save_all_data(self, data: dict, tables: List[str]):
        for table_name in tables:
            rows: list = []
            fields_names = list(key for key in data[table_name][0].__dataclass_fields__)
            rows.append(fields_names)
            for row_data in data[table_name]:
                row = []
                for field_name in fields_names:
                    row.append(getattr(row_data, field_name))
                rows.append(row)
            self._save_data_to_table(table_name=table_name,
                                     rows=rows)
            # break


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    sqlite_loader = SQLiteLoader(connection)
    data = sqlite_loader.load_movies()

    postgres_saver = PostgresSaver(pg_conn)
    tables = [
        'film_work',
        'genre',
        'person',
        'genre_film_work',
        'person_film_work',
    ]
    postgres_saver.save_all_data(data, tables)


def main():
    try:
        script_params = load_params(
            required_params=[
                "dbname",
                "user",
                "password",
                "host",
                "port",
                "db_sqlite_file",
            ])
        # logger.info(script_params)
        dsl = {'dbname': script_params['dbname'],
               'user': script_params['user'],
               'password': script_params['password'],
               'host': script_params['host'],
               'port': script_params['port'],
               'options': '-c search_path=content'}
        sqlite_file = script_params['db_sqlite_file']
        if not os.path.isfile(sqlite_file):
            raise sqlite3.OperationalError
        with sqlite3.connect(script_params['db_sqlite_file'], uri=True) as sqlite_conn:
            with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
                load_from_sqlite(sqlite_conn, pg_conn)

    except sqlite3.OperationalError:
        logger.error("Can't open sqlite file")

    except psycopg2.OperationalError as e:
        logger.error(e)


if __name__ == '__main__':
    main()
