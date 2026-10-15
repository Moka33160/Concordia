"""
File: city.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: A city of the board, holding its token and the houses built in it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.models.resource import Good
from concordia.models.token import CityToken

if TYPE_CHECKING:
    from concordia.models.colonist import Colonist


class City:
    """A city of the map."""

    def __init__(self, name: str, letter: str, nb_house_max: int,
                 x: int = 0, y: int = 0):
        self.name = name
        self.letter = letter
        self.nb_house_max = nb_house_max
        self.x = x
        self.y = y
        self.token = None
        self.houses = []
        self.colonists = []

    def set_token(self, token: CityToken) -> None:
        """Put a city token on the city."""
        if token.roman_char != self.letter:
            raise ValueError(
                f"{token.roman_char!r} token does not fit the "
                f"{self.letter!r} city {self.display_name!r}"
            )
        self.token = token

    def reveal(self) -> Good:
        """Turn the token of the city face up."""
        if self.token is None:
            raise ValueError(f"{self.display_name!r} has no token to reveal")
        return self.token.reveal()

    @property
    def display_name(self) -> str:
        """The name without the padding the database adds to the capital."""
        return " ".join(self.name.split())

    @property
    def good(self) -> Good | None:
        """
        The good produced by the city, or None while the token is missing.
        """
        return None if self.token is None else self.token.good

    @property
    def is_full(self) -> bool:
        """Whether every house slot of the city is taken."""
        return len(self.houses) >= self.nb_house_max

    def __repr__(self) -> str:
        return f"City({self.display_name!r}, {self.letter!r})"

    def get_nb_house(self) -> int:
        """Return how many houses are already built in the city."""
        return len(self.houses)

    def add_house(self, house) -> None:
        """Build a house in the city."""
        self.houses.append(house)

    def add_colonist(self, colonist: Colonist) -> None:
        """Place a colonist in the city."""
        self.colonists.append(colonist)

    def remove_colonist(self, colonist: Colonist) -> None:
        """Take a colonist off the city, when it moves away."""
        if colonist in self.colonists:
            self.colonists.remove(colonist)

    def get_name(self) -> str:
        """Return the city's database name, padding included."""
        return self.name

    def get_token(self) -> CityToken:
        """Return the city's token, or None if it hasn't been dealt yet."""
        return self.token

    def get_nb_house_max(self) -> int:
        """Return the maximum number of houses the city can hold."""
        return self.nb_house_max
