"""
File: province.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: A province of the map, grouping cities under one bonus marker.
"""
from concordia.models.city import City
from concordia.models.resource import Good
from concordia.models.token import BonusMarker


class Province:
    """A province of the map, identified by its roman numeral."""

    def __init__(self, name: str, roman_num: str, x: int = 0, y: int = 0):
        self.name = name
        self.roman_num = roman_num
        self.x = x
        self.y = y
        self.cities = []
        self.bonus_marker = None
        # A province starts face up, so the PREFECT can produce in it.
        self.is_flipped = False

    def add_city(self, city: City) -> None:
        """Attach a city to the province."""
        self.cities.append(city)

    def most_valuable_good(self) -> Good | None:
        """
        Look up the most valuable good produced among the cities of the
        province.
        """
        goods = [city.good for city in self.cities if city.good is not None]
        return max(goods, key=lambda good: good.value, default=None)

    def set_bonus_marker(self, marker: BonusMarker) -> None:
        """Give the province its bonus marker."""
        self.bonus_marker = marker

    def __repr__(self) -> str:
        return f"Province({self.name!r}, {self.roman_num!r})"
