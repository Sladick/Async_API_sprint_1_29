from http import HTTPStatus

from pydantic import UUID4, BaseModel

from fastapi import APIRouter, Depends, HTTPException

from services.common import CommonQueryParams
from services.film import FilmService, get_film_service
from services.filmdependencies import GenreFilter, MatchQuery, FilmQuery

router = APIRouter()


class Genre(BaseModel):
    uuid: UUID4
    name: str


class Person(BaseModel):
    uuid: UUID4
    full_name: str


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float = 0
    description: str
    genre: list[Genre] = []
    actors: list[Person] = []
    writers: list[Person] = []
    directors: list[Person] = []


class FilmForList(BaseModel):
    id: str
    title: str
    imdb_rating: float = 0


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: UUID4, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="film not found")

    return Film(
        id=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        actors=[Person(uuid=p.id, full_name=p.name) for p in film.actors],
        writers=[Person(uuid=p.id, full_name=p.name) for p in film.writers],
        directors=[Person(uuid=p.id, full_name=p.name) for p in film.directors],
        genre=[Genre(uuid=g.id, name=g.name) for g in film.genre],
    )


@router.get("/", response_model=list[FilmForList])
async def films_details_cache(
    filter_: GenreFilter = Depends(GenreFilter),
    commons: CommonQueryParams = Depends(CommonQueryParams),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmForList]:

    films = await film_service.get_films(commons=commons, filter_=filter_, cache_=True)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="bad parameters")

    return [
        FilmForList(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]


@router.get("/search/", response_model=list[FilmForList])
async def films_details_no_cache(
    match_query: MatchQuery = Depends(MatchQuery),
    commons: CommonQueryParams = Depends(CommonQueryParams),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmForList]:

    films = await film_service.get_films(match_query=match_query, commons=commons, cache_=False)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="mo matches")

    return [
        FilmForList(id=film.id, title=film.title, imdb_rating=film.imdb_rating)
        for film in films
    ]
