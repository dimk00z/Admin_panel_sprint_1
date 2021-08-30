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
schema=content
```

Структура решения:

* основной скрипт для переноса
  данных: [load_data.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/load_data.py)
* описаны dataclass согласно структуре базы
  данных: [utils/dataclasses.py](https://github.com/dimk00z/Admin_panel_sprint_1/blob/master/sqlite_to_postgres/utils/dataclasses.py)

## Выполнение

Загрузка производится по `page_size` элементов, дубликаты игнорируются. Пример выполнения:

```
python load_data.py
INFO:load_data.py:Data loaded from table: film_work, 999 rows
INFO:load_data.py:Data loaded from table: genre, 26 rows
INFO:load_data.py:Data loaded from table: person, 4166 rows
INFO:load_data.py:Data loaded from table: genre_film_work, 2231 rows
INFO:load_data.py:Data loaded from table: person_film_work, 5783 rows
INFO:load_data.py:All tables were loaded from sqlite
INFO:load_data.py:Uploaded 999 rows for table:film_work
INFO:load_data.py:Uploaded 26 rows for table:genre
INFO:load_data.py:Uploaded 4166 rows for table:person
INFO:load_data.py:Uploaded 2231 rows for table:genre_film_work
INFO:load_data.py:Uploaded 5783 rows for table:person_film_work
INFO:load_data.py:All tasks have worked correctly

```
