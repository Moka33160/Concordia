"""
File: colonist.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: A colonist, either kept in a player's storehouse or standing
             somewhere on the board.
"""
from __future__ import annotations

from concordia.models.city import City
from concordia.models.route import Route


class Colonist:
    """A colonist, moving on the land or sea routes of the board."""

    def __init__(self, way: str):
        self.way = way
        self.position: City | Route | None = None

    @property
    def is_placed(self) -> bool:
        """Whether the colonist is out of the storehouse and on the board."""
        return self.position is not None

    @property
    def city(self) -> City | None:
        """The city the colonist is standing in."""
        return self.position if isinstance(self.position, City) else None

    @property
    def route(self) -> Route | None:
        """
        The route the colonist is standing on, None while still in a city.
        """
        return self.position if isinstance(self.position, Route) else None

    def place(self, position: City | Route) -> None:
        """
        Stand the colonist on a city or a route, taking it off the last one.
        """
        if self.position is not None and self in self.position.colonists:
            self.position.colonists.remove(self)

        self.position = position

        if self not in position.colonists:
            position.colonists.append(self)

    def __repr__(self) -> str:
        return f"Colonist({self.way!r})"
