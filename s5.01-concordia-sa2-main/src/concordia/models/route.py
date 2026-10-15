"""
File: route.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: A route of the board: the line drawn between two cities, and the
             colonists standing on it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from concordia.models.city import City
    from concordia.models.colonist import Colonist


class Route:
    """One route between two cities, of one way: land, sea or air."""

    def __init__(self, city_a: City, city_b: City, kind: str):
        self.city_a = city_a
        self.city_b = city_b
        self.kind = kind
        self.colonists: list[Colonist] = []

    @property
    def cities(self) -> tuple[City, City]:
        """The two cities the route joins, which are its two ends."""
        return self.city_a, self.city_b

    def touches(self, city: City) -> bool:
        """Whether the route ends on a city."""
        return city is self.city_a or city is self.city_b

    def other_end(self, city: City) -> City | None:
        """The city at the far end of the route."""
        if city is self.city_a:
            return self.city_b
        if city is self.city_b:
            return self.city_a
        return None

    def is_adjacent(self, other: Route) -> bool:
        """
        Whether a colonist on this route can step onto another in one move.
        """
        return other is not self and any(
            other.touches(city) for city in self.cities
        )

    @property
    def display_name(self) -> str:
        """The route named by its two ends, for a prompt to read out."""
        return (
            f"{self.city_a.display_name}–{self.city_b.display_name}"
            f" ({self.kind})"
        )

    def __iter__(self):
        return iter((self.city_a, self.city_b, self.kind))

    def __getitem__(self, index: int):
        return (self.city_a, self.city_b, self.kind)[index]

    def __repr__(self) -> str:
        return (
            f"Route({self.city_a.display_name!r}, "
            f"{self.city_b.display_name!r}, {self.kind!r})"
        )
