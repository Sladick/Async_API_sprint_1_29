from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi_redis_cache import cache

from services.common import CommonQueryParams, GenreFilter
from services.film import FilmService, get_film_service

router = APIRouter()


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float = 0


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)


@router.get("/", response_model=list[Film])
async def film_details(
    commons: CommonQueryParams = Depends(CommonQueryParams),
    filter_: GenreFilter = Depends(GenreFilter),
    film_service: FilmService = Depends(get_film_service),
) -> list[Film]:
    films = await film_service.get_films(commons, filter_)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return [
        Film(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
