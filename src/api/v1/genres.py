from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.models.mixins import UUIDMixin
from src.models.genre import GenreIDQueryParams
from src.services.genre import GenreService, get_genre_service
from src.services.common import CommonQueryParamsMixin

router = APIRouter()


class GenresList(UUIDMixin):
    name: str


class GenreDetails(UUIDMixin):
    name: str
    description: Optional[str] = None


@router.get("/", response_model=List[GenresList])
async def genre_list(common: CommonQueryParamsMixin = Depends(),
                     genre_service: GenreService = Depends(get_genre_service)) -> List[GenresList]:
    genres = await genre_service.get_genres(common)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genres not found")

    return [GenresList(**genre.dict()) for genre in genres]


@router.get("/{genre_id}", response_model=GenreDetails)
async def genre_details(common: GenreIDQueryParams = Depends(GenreIDQueryParams),
                        genre_service: GenreService = Depends(get_genre_service)) -> GenreDetails:
    genre = await genre_service.get_genre_by_id(common.id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Genre not found")

    return GenreDetails(**genre.dict())
