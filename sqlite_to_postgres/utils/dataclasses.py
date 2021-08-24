from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Film_Work:
    title: str
    description: str
    created_at: datetime
    old_id: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    rating: float = field(default=0.0)


@dataclass
class Genre:
    name: str
    created_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Person:
    name: str
    old_id: str
    created_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Film_Work_Peson:
    id_film: uuid.UUID
    id_person: uuid.UUID
    old_id_film: str
    old_id_person: str


@dataclass
class Film_Work_Genre:
    id_film: uuid.UUID
    id_genre: uuid.UUID
    id: uuid.UUID = field(default_factory=uuid.uuid4)
