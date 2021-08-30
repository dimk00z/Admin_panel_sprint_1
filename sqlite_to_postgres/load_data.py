import logging
import os
import sqlite3
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from os import environ
from typing import Dict, List, Tuple

import psycopg2
from dacite import from_dict
from dateutil import parser
from dotenv import load_dotenv
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor, execute_values

from utils.dataclasses import (FilmWork, FilmWorkGenre, FilmWorkPerson, Genre,
                               Person)

logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.DEBUG)


class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection,
                 classes_per_table: Dict[str, dataclass]) -> None:
        self.cursor: connection.cursor = connection.cursor()
        self.classes_per_table = classes_per_table

        self.sqlite_data: Dict[str, List[str]] = {}

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

    def _sanitize_table_data(self,
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
                    current_record[key] = current_record[key].replace(
                        "'", "''")
            current_table_data.append(
                from_dict(data_class=data_class_name,
                          data=current_record))

        return current_table_data

    def _sanitize_data(self) -> Dict[str, List[dataclass]]:
        sanitized_data: Dict[str:] = {}
        for table_name, data_class_name in self.classes_per_table.items():
            logger.info(f'Loading from table: {table_name}')
            sanitized_data[table_name] = self._sanitize_table_data(
                table_name=table_name, data_class_name=data_class_name
            )
        return sanitized_data

    def load_movies(self) -> Dict[str, List[dataclass]]:
        self._load_all_sqlite_data()
        data: Dict[str:List[dataclass]] = self._sanitize_data()
        logger.info('Data loaded from sqlite db')
        return data


class PostgresSaver:
    def __init__(self, pg_conn: _connection,
                 page_size: int, schema: str = 'content'):
        self.cursor = pg_conn.cursor()
        self.schema = schema
        self.page_size = page_size

    def _save_data_to_table(self, table_name: str,
                            table_data: List[dataclass]) -> None:
        logger.info(f'Uploading into table: {table_name}')
        dataclass_fields: Tuple[str] = tuple(
            table_data[0].__dataclass_fields__.keys())
        rows_names: str = ', '.join(dataclass_fields)

        rows_for_script: List[tuple] = []
        for entry in table_data:
            row: List[str, None] = []
            for field_name in dataclass_fields:
                row.append(str(getattr(entry, field_name)) if getattr(entry,
                                                                      field_name) else None)
            rows_for_script.append(tuple(row))

        execute_values(
            cur=self.cursor,
            sql=f'''INSERT INTO {self.schema}.{table_name} ({rows_names}) 
                VALUES %s 
                ON CONFLICT (id) DO NOTHING''',
            argslist=rows_for_script, page_size=self.page_size)
        table_size = len(table_data)
        logger.info(
            f'Loaded page {table_size} rows for table:{table_name}')

    def save_all_data(self, data: dict, tables: Tuple[str]) -> None:
        for table_name in tables:
            self._save_data_to_table(
                table_name=table_name,
                table_data=data[table_name])


def main():
    load_dotenv()
    dsl: Dict[str:str] = {
        'dbname': environ.get('dbname'),
        'user': environ.get('user'),
        'password': environ.get('password'),
        'host': environ.get('host'),
        'port': environ.get('port'),
        'options': '-c search_path=content'
    }
    sqlite_file: str = environ.get('db_sqlite_file')

    classes_per_table: OrderedDict = OrderedDict(
        [('film_work', FilmWork),
         ('genre', Genre),
         ('person', Person),
         ('genre_film_work', FilmWorkGenre),
         ('person_film_work', FilmWorkPerson)]
    )
    tables_names: Tuple[str] = tuple(map(str, classes_per_table.keys()))

    try:
        if not os.path.isfile(sqlite_file):
            raise OSError
        with sqlite3.connect(sqlite_file) as sqlite_conn:
            sqlite_loader: SQLiteLoader = SQLiteLoader(
                connection=sqlite_conn,
                classes_per_table=classes_per_table)
            data: Dict[str:List[dataclass]] = sqlite_loader.load_movies()
    except OSError:
        logger.exception('Have a problem with sqlite file')
    except sqlite3.OperationalError as ex:
        logger.exception(ex)
    finally:
        sqlite_conn.close()

    try:
        with psycopg2.connect(**dsl, cursor_factory=DictCursor) as pg_conn:
            postgres_saver: PostgresSaver = PostgresSaver(
                pg_conn=pg_conn,
                page_size=int(environ.get('page_size')),
                schema=environ.get('schema'))
            postgres_saver.save_all_data(data=data,
                                         tables=tables_names)
    except psycopg2.Error as e:
        logger.exception(e.pgerror)

    finally:
        pg_conn.close()

    logger.info('All tasks have worked correctly')


if __name__ == '__main__':
    main()
