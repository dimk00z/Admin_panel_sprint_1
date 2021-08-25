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

from typing import List, Tuple, Dict

import sqlite3

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

MAX_OPERATION_PER_PAGE = 500
SCHEMA = 'content'

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

    def _get_table_data(self,
                        table_name: str,
                        data_class_name: dataclass) -> List[dataclass]:

        keys: dict = {key: {'position': position} for
                      position, key in enumerate(self.sqlite_data[table_name][0])}
        current_table_data: List[dataclass] = []

        for key in keys:
            keys[key]['type'] = data_class_name.__dataclass_fields__[key].type

        for row in self.sqlite_data[table_name][1:]:
            current_record: dict = {
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
                elif keys[key]['type'] == str:
                    current_record[key] = current_record[key].replace("'", "''")
            current_table_data.append(
                from_dict(data_class=data_class_name,
                          data=current_record))

        return current_table_data

    def _sanitize_data(self) -> Dict[str, List[dataclass]]:
        sanitized_data: Dict[str:] = {}
        classes_per_table: Dict[str:dataclass] = {
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

    def load_movies(self) -> Dict[str, List[dataclass]]:
        self._load_all_sqlite_data()
        data: Dict[str:List[dataclass]] = self._sanitize_data()
        logger.info('Data loaded from sqlite db')
        return data


class PostgresSaver:
    def __init__(self, pg_conn: _connection):
        self.cursor = pg_conn.cursor()

    def _save_data_to_table(self, table_name: str,
                            table_data: List[dataclass]) -> None:
        logger.debug(table_name)
        dataclass_fields: Tuple[str] = tuple(table_data[0].__dataclass_fields__.keys())
        rows_names: str = ', '.join(dataclass_fields)

        grouped_table_data = group_elements(table_data[1:],
                                            MAX_OPERATION_PER_PAGE)
        for page_number, rows in enumerate(grouped_table_data):

            rows_for_script: List[str] = []
            for data_class in rows:
                row: List[str] = []
                for field_name in dataclass_fields:
                    row.append("'{}'".format(
                        str(getattr(data_class, field_name))) if getattr(data_class,
                                                                         field_name) else "NULL")
                rows_for_script.append('({})'.format(', '.join(row)))

            sql_template: str = '\n'.join(
                (f"INSERT INTO {SCHEMA}.{table_name} ({rows_names})\nVALUES ",
                 ', \n'.join(rows_for_script),
                 'ON CONFLICT (id) DO NOTHING;'))
            self.cursor.execute(sql_template)
            rows_count = len(rows)
            logger.info(f'Loaded page #{page_number + 1}:{rows_count} rows for table:{table_name}')

    def save_all_data(self, data: dict) -> None:
        for table_name, table_data in data.items():
            self._save_data_to_table(
                table_name=table_name,
                table_data=table_data)


def load_from_sqlite(connection: sqlite3.Connection,
                     pg_conn: _connection) -> None:
    """Основной метод загрузки данных из SQLite в Postgres"""
    sqlite_loader: SQLiteLoader = SQLiteLoader(connection)
    data: Dict[str:List[dataclass]] = sqlite_loader.load_movies()

    postgres_saver: PostgresSaver = PostgresSaver(pg_conn)
    postgres_saver.save_all_data(data)


def main():
    try:
        script_params: Dict[str] = load_params(
            required_params=[
                "dbname",
                "user",
                "password",
                "host",
                "port",
                "db_sqlite_file",
            ])
        logger.debug(script_params)
        dsl: Dict[str:str] = {
            'dbname': script_params['dbname'],
            'user': script_params['user'],
            'password': script_params['password'],
            'host': script_params['host'],
            'port': script_params['port'],
            'options': '-c search_path=content'
        }
        sqlite_file: str = script_params['db_sqlite_file']
        if not os.path.isfile(sqlite_file):
            raise OSError
        with sqlite3.connect(script_params['db_sqlite_file']) as sqlite_conn:
            with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
                load_from_sqlite(sqlite_conn, pg_conn)

    except OSError:
        logger.error('Have a problem with sqlite file')

    except sqlite3.OperationalError as ex:
        logger.error(ex)

    except (psycopg2.OperationalError, psycopg2.errors) as e:
        logger.error(e)


if __name__ == '__main__':
    main()
