from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class FilmWork:
    title: str
    description: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    rating: float = field(default=0.0)
    created_at: datetime = field(default_factory=datetime.now)
    type: str = field(default="movie")


@dataclass
class Genre:
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Person:
    full_name: str
    created_at: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class FilmWorkPerson:
    id_film: uuid.UUID
    id_person: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FilmWorkGenre:
    id_film: uuid.UUID
    id_genre: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
