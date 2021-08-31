import logging
import os
import sqlite3
from collections import OrderedDict
from dataclasses import dataclass
from os import environ
from typing import Dict, List, Tuple

import psycopg2
from dacite import from_dict
from dotenv import load_dotenv
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor, execute_values

from utils.dataclasses import (FilmWork, FilmWorkGenre, FilmWorkPerson, Genre,
                               Person, sanitize_field)

logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.DEBUG)


class SQLiteLoader:
    def __init__(self, connection: sqlite3.Connection,
                 classes_per_table: Dict[str, dataclass],
                 tables_names: Tuple[str]) -> None:
        connection.row_factory = lambda c, r: dict(
            zip([col[0] for col in c.description], r))
        self.cursor: connection.cursor = connection.cursor()

        self.classes_per_table = classes_per_table
        self.tables_names = tables_names

    def _load_table(self, table_name: str) -> List[dataclass]:
        current_table: List[dataclass] = []
        self.cursor.execute(f'SELECT * FROM {table_name}')

        current_value_type: dict = self.classes_per_table[
            table_name].__annotations__.items()

        while True:
            next_row = self.cursor.fetchone()
            if next_row:
                for field_name, field_type in current_value_type:
                    if next_row[field_name] is None:
                        del next_row[field_name]
                    else:
                        next_row[field_name] = sanitize_field(
                            field_type=field_type,
                            field_value=next_row[field_name])
                current_table.append(
                    from_dict(self.classes_per_table[table_name], next_row)
                )
            else:
                logger.info(
                    'Data loaded from table: {}, {} rows'.format(table_name, len(current_table)))
                return current_table

    def load_movies(self) -> Dict[str, List[dataclass]]:
        movies_data: Dict[str:List[dataclass]] = {}
        for table_name in self.tables_names:
            movies_data[table_name] = self._load_table(table_name)
        logger.info('All tables were loaded from sqlite')
        return movies_data


class PostgresSaver:
    def __init__(self, pg_conn: _connection,
                 page_size: int, schema: str = 'content'):
        self.cursor = pg_conn.cursor()
        self.schema = schema
        self.page_size = page_size

    def _save_data_to_table(self, table_name: str,
                            table_data: List[dataclass]) -> None:
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
            argslist=rows_for_script,
            page_size=self.page_size)
        table_size = len(table_data)
        logger.info(
            f'Uploaded {table_size} rows for table:{table_name}')

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

    if not os.path.isfile(sqlite_file):
        raise OSError('Have a problem with sqlite file')

    try:
        with sqlite3.connect(sqlite_file) as sqlite_conn:
            sqlite_loader: SQLiteLoader = SQLiteLoader(
                connection=sqlite_conn,
                classes_per_table=classes_per_table,
                tables_names=tables_names)
            data: Dict[str:List[dataclass]] = sqlite_loader.load_movies()
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
