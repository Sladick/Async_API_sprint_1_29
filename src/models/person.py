import uuid

from pydantic import BaseModel, Field, validator

from src.models.mixins import OrjsonConfigMixin, UUIDMixin


class Person(UUIDMixin, OrjsonConfigMixin):
    full_name: str


class PersonIDQueryParams(BaseModel):
    id: str = Field(..., alias='person_id')

    @validator('id')
    def is_valid_uuid(cls, v):
        try:
            return uuid.UUID(v)
        except ValueError:
            raise ValueError('person_id must by format uuid version 4')
