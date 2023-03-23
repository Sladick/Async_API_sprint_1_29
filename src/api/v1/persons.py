from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.models.mixins import UUIDMixin
from src.models.person import PersonIDQueryParams
from src.services.person import PersonService, get_person_service
from src.services.common import CommonQueryParamsMixin

router = APIRouter()


class Person(UUIDMixin):
    full_name: str


@router.get("/", response_model=List[Person])
async def person_list(commons: CommonQueryParamsMixin = Depends(CommonQueryParamsMixin),
                      person_service: PersonService = Depends(get_person_service)) -> List[Person]:
    persons = await person_service.get_persons(commons)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Persons not found")

    return [Person(**person.dict()) for person in persons]


@router.get("/{person_id}", response_model=Person)
async def person_details(commons: PersonIDQueryParams = Depends(PersonIDQueryParams),
                         person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_person_by_id(commons.id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Person not found")

    return Person(**person.dict())
