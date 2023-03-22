import uuid
from typing import Optional

from pydantic import BaseModel, Field, validator

from src.models.mixins import OrjsonConfigMixin, UUIDMixin


class Genre(UUIDMixin, OrjsonConfigMixin):
    name: str = Field(alias='genre_name')
    description: Optional[str] = None


class GenreIDQueryParams(BaseModel):
    id: str = Field(..., alias='genre_id')

    @validator('id')
    def is_valid_uuid(cls, v):
        try:
            return uuid.UUID(v)
        except ValueError:
            raise ValueError('genre_id must by format uuid version 4')
