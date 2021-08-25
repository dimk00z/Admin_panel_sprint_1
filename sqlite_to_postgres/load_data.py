import os
import logging
from dacite import from_dict
from datetime import datetime
from dateutil import parser
import uuid
from utils.dataclasses import FilmWork, Person, Genre, FilmWorkPerson, FilmWorkGenre
from utils.list_utils import group_elements
from utils.env_load import load_params
from dataclasses import dataclass

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

    def _get_table_data(self, table_name: str, data_class_name: dataclass):
        keys = {key: {'position': position} for
                position, key in enumerate(self.sqlite_data[table_name][0])}
        current_table_data = []
        for key in keys:
            keys[key]['type'] = data_class_name.__dataclass_fields__[key].type

        for row in self.sqlite_data[table_name][1:]:
            current_record = {
                key: row[keys[key]['position']]
                for key in keys if row[keys[key]['position']]
            }
            for key in current_record:
                if keys[key]['type'] == datetime:
                    current_record[key] = parser.isoparse(current_record[key])
                elif keys[key]['type'] == float:
                    current_record[key] = float(current_record[key])
                elif keys[key]['type'] == uuid.UUID:
                    current_record[key] = uuid.UUID(current_record[key])
            current_table_data.append(
                from_dict(data_class=data_class_name, data=current_record))
        return current_table_data

    def _sanitize_data(self) -> dict:
        sanitized_data: dict = {}
        classes_per_table = {
            'film_work': FilmWork,
            'genre': Genre,
            'person': Person,
            'genre_film_work': FilmWorkGenre,
            'person_film_work': FilmWorkPerson,
        }
        for table_name, data_class_name in classes_per_table.items():
            logger.debug(table_name)
            sanitized_data[table_name] = self._get_table_data(
                table_name=table_name, data_class_name=data_class_name
            )

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

                # excluded_str = ', '.join([f'{name}=EXCLUDED.{name}' for name in rows[0]])
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
                break


def load_from_sqlite(connection: sqlite3.Connection, pg_conn: _connection):
    """Основной метод загрузки данных из SQLite в Postgres"""
    sqlite_loader = SQLiteLoader(connection)
    data = sqlite_loader.load_movies()
    for some, value in data.items():
        print(some, value[0])

    # postgres_saver = PostgresSaver(pg_conn)
    # tables = [
    #     'film_work',
    #     'genre',
    #     'person',
    #     'genre_film_work',
    #     'person_film_work',
    # ]
    # postgres_saver.save_all_data(data, tables)


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
        with sqlite3.connect(script_params['db_sqlite_file']) as sqlite_conn:
            with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
                load_from_sqlite(sqlite_conn, pg_conn)

    except sqlite3.OperationalError as ex:
        logger.error(ex)

    except psycopg2.OperationalError as e:
        logger.error(e)


if __name__ == '__main__':
    main()
