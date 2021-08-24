from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Film_Work:
    title: str
    description: str
    old_id: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    rating: float = field(default=0.0)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Genre:
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Person:
    full_name: str
    old_id: str
    created_at: datetime = field(default_factory=datetime.now)
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class FilmWorkPerson:
    id_film: uuid.UUID
    id_person: uuid.UUID
    old_id_film: str
    old_id_person: str


@dataclass
class FilmWorkGenre:
    id_film: uuid.UUID
    id_genre: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
