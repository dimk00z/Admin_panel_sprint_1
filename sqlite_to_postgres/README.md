# Техническое задание

Как только вы выполнили новые задания по работе с Postgres, к вам снова прибежал продакт. Он просит
перенести уже заведённые карточки фильмы в новое хранилище, чтобы контент-менеджеры обновили
недостающие описания, когда появится админка.

Совсем недавно вы спроектировали схему данных для Postgres, с которой гораздо проще работать, но
SQLite всё так же живёт со сломанной схемой. Нужно аккуратно переложить данные, но при этом ничего
не потерять при загрузке. Продакт верит, что вы сможете сделать это в ближайшие дни. Что ж, пришло
время показать на что вы способны!

На первый взгляд задача выглядит простой: взять данные из одной базы и переложить в другую — даже
бизнес-логики в этом нет! Но присмотритесь к задаче внимательно, ведь в ней полно важных моментов:

1. Нужно сохранить данные в пять разных таблиц в Postgres — `film_work`, `genre`, `person`
   , `film_work_genre`, `film_work_person` — из четырёх таблиц в SQLite — `movies`, `movie_actors`
   , `actors`, `writers`.
2. Нужно придумать, как проще всего извлечь данные из SQLite.

> Совет: воспользуйтесь способом, который вы использовали в бесплатной части курса.

3. Нужно написать набор функций для преобразования данных из SQLite в Postgres. Это основная часть
   приложения, поэтому стройте всю программу от этой части.
4. В SQLite основная таблица — `movies`. Постарайтесь склеивать остальные таблицы с данными из
   таблицы movies — это может сильно помочь.
5. `dataclass` поможет быстро понять, где возникает ошибка при работе с данными.
6. Для генерации `id`в таблицах Postgres лучше всего использовать `uuid.uuid4()`.
7. Подумайте, как можно сделать загрузку данных пачками, а не целиком.

> 7 задание со звёздочкой :)

# Решение 2 проектного задания

## Описание

Для переноса данных написан
скрипт [load_data.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/load_data.py)

## Настройка и выполнение

Работоспособность проверена на Python 3.8. Установка зависимостей `pip install -r requirements.txt`

Для работы необходимо наличие .env файла в текущей директории для загрузки параметров:

```
dbname=online_movie_theater_db
user=postgres
password=<your_password>
host=localhost
port=5432
db_sqlite_file=db.sqlite
page_size=1000
```

Структура решения:

* [load_data.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/load_data.py)
    - основной скрипт для переноса данных
* [utils/dataclasses.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/utils/dataclasses.py)
    - описаны dataclass согласно структуры базы данных
* [utils/list_utils.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/utils/list_utils.py)
    - функция группировки списков
* [utils/env_load.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/utils/env_load.py)
    - загрузка параметров с .env

## Выполнение

Загрузка производится по `page_size` элементов, дубликаты игнорируются. Пример выполнения:

```
python load_data.py
INFO:load_data.py:Loaded parameters: ('dbname', 'user', 'password', 'host', 'port', 'db_sqlite_file', 'page_size')
INFO:load_data.py:Loading from table: film_work
INFO:load_data.py:Loading from table: genre
INFO:load_data.py:Loading from table: person
INFO:load_data.py:Loading from table: genre_film_work
INFO:load_data.py:Loading from table: person_film_work
INFO:load_data.py:Data loaded from sqlite db
INFO:load_data.py:Uploading into table: film_work
INFO:load_data.py:Loaded page #1:998 rows for table:film_work
INFO:load_data.py:Uploading into table: genre
INFO:load_data.py:Loaded page #1:25 rows for table:genre
INFO:load_data.py:Uploading into table: person
INFO:load_data.py:Loaded page #1:1000 rows for table:person
INFO:load_data.py:Loaded page #2:1000 rows for table:person
INFO:load_data.py:Loaded page #3:1000 rows for table:person
INFO:load_data.py:Loaded page #4:1000 rows for table:person
INFO:load_data.py:Loaded page #5:165 rows for table:person
INFO:load_data.py:Uploading into table: genre_film_work
INFO:load_data.py:Loaded page #1:1000 rows for table:genre_film_work
INFO:load_data.py:Loaded page #2:1000 rows for table:genre_film_work
INFO:load_data.py:Loaded page #3:230 rows for table:genre_film_work
INFO:load_data.py:Uploading into table: person_film_work
INFO:load_data.py:Loaded page #1:1000 rows for table:person_film_work
INFO:load_data.py:Loaded page #2:1000 rows for table:person_film_work
INFO:load_data.py:Loaded page #3:1000 rows for table:person_film_work
INFO:load_data.py:Loaded page #4:1000 rows for table:person_film_work
INFO:load_data.py:Loaded page #5:1000 rows for table:person_film_work
INFO:load_data.py:Loaded page #6:782 rows for table:person_film_work
```
