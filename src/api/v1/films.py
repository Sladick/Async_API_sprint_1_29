from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4

from src.models.mixins import UUIDMixin
from src.services.common import CommonQueryParams
from src.services.film import FilmService, get_film_service
from src.services.filmdependencies import GenreFilter, MatchQuery, FilmQuery

router = APIRouter()


class Genre(UUIDMixin):
    name: str


class Person(UUIDMixin):
    name: str


class Film(UUIDMixin):
    title: str
    imdb_rating: float = 0
    description: str
    genre: list[Genre] = []
    actors: list[Person] = []
    writers: list[Person] = []
    directors: list[Person] = []


class FilmForList(UUIDMixin):
    title: str
    imdb_rating: float = 0


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: UUID4, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return Film(**film.dict())


@router.get("/", response_model=list[FilmForList])
async def films_details_cache(
    filter_: GenreFilter = Depends(GenreFilter),
    commons: CommonQueryParams = Depends(CommonQueryParams),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmForList]:

    films = await film_service.get_films(commons=commons, filter_=filter_, cache_=True)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="bad parameters")

    return [FilmForList(**film.dict()) for film in films]


@router.get("/search/", response_model=list[FilmForList])
async def films_details_no_cache(
    match_query: MatchQuery = Depends(MatchQuery),
    commons: CommonQueryParams = Depends(CommonQueryParams),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmForList]:

    films = await film_service.get_films(match_query=match_query, commons=commons, cache_=False)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="mo matches")

    return [FilmForList(**film.dict()) for film in films]
