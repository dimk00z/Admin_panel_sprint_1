from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Dict
import uuid


@dataclass
class FilmWork:
    title: str
    description: str = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    creation_date: str = None
    certificate: str = None
    file_path: str = None
    rating: float = field(default=0.0)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    type: str = field(default="movie")


@dataclass
class Genre:
    name: str
    description: str = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Person:
    full_name: str
    birth_date: str = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class FilmWorkPerson:
    film_work_id: uuid.UUID
    person_id: uuid.UUID
    role: str = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FilmWorkGenre:
    film_work_id: uuid.UUID
    genre_id: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)


classes_per_table: Dict[str:dataclass] = {
    'film_work': FilmWork,
    'genre': Genre,
    'person': Person,
    'genre_film_work': FilmWorkGenre,
    'person_film_work': FilmWorkPerson,
}
