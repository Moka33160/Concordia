"""
File: board.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The board for the game, holding the provinces, the cities and the
             routes between them.
"""
import random

from concordia.models.city import City
from concordia.models.province import Province
from concordia.models.route import Route
from concordia.models.token import BonusMarker, CityToken
from concordia.models.way import Way


class Board:
    """The board for the game: the map's provinces, cities and routes."""

    def __init__(self, map_name: str):
        self.map = map_name
        self.capital = None
        self.provinces = []
        self.routes = []
        self._cities = {}
        self.ways = []
        self.way_colors: dict[str, str] = {}
        self.max_x = 0
        self.max_y = 0

    def set_way_colors(self, way_colors: dict[str, str]) -> None:
        """Attach the display colour of every way (land, sea, air)."""
        self.way_colors = way_colors

    def set_bounds(self, max_x: int, max_y: int) -> None:
        """
        Set the coordinate system's extent, so a view can scale it to fit.

        :param max_x: The largest x coordinate used on this map.
        :param max_y: The largest y coordinate used on this map.
        """
        self.max_x = max_x
        self.max_y = max_y

    def set_capital(self, capital: City) -> None:
        """Set the capital of the map (Roma, or Bordeaux on the EU map)."""
        self.capital = capital
        self.index_city(capital)

    def add_province(self, province: Province) -> None:
        """Add a province to the board."""
        self.provinces.append(province)

    def index_city(self, city: City) -> None:
        """Make a city reachable by name, so routes can resolve it later."""
        self._cities[city.name] = city

    def city(self, name: str) -> City:
        """Look up a city by its exact database name."""
        return self._cities[name]

    def cities(self) -> list[City]:
        """Every city of the board, capital included."""
        return list(self._cities.values())

    def add_route(self, city_a: str, city_b: str, kind: str) -> None:
        """
        Add a route between two cities, resolved by name.

        :param city_a: Name of the first city.
        :param city_b: Name of the second city.
        :param kind: The way of the route (land, sea or air).
        """
        self.routes.append(Route(self.city(city_a), self.city(city_b), kind))

    def routes_at(self, city: City, way: str | None = None) -> list[Route]:
        """
        Every route running out of a city.

        :param city: The city to look the routes up from.
        :param way: The way to keep, None for every way.
        :return: The routes ending on that city.
        """
        return [
            route for route in self.routes
            if route.touches(city) and (way is None or route.kind == way)
        ]

    def routes_next_to(self, route: Route,
                       way: str | None = None) -> list[Route]:
        """
        Every route one step away from a route.

        :param route: The route being stepped off.
        :param way: The way to keep, None for every way.
        :return: The routes a colonist on it can step onto.
        """
        return [
            other for other in self.routes
            if route.is_adjacent(other) and (way is None or other.kind == way)
        ]

    def get_route_kind(self, city_a: City, city_b: City) -> str | None:
        """
        Return the kind of route between two cities.

        :param city_a: The first city.
        :param city_b: The second city.
        :return: The route kind, or None if no route exists.
        """
        for route_city_a, route_city_b, kind in self.routes:
            if ((route_city_a == city_a and route_city_b == city_b)
                    or (route_city_a == city_b and route_city_b == city_a)):
                return kind

        return None

    def add_way(self, name: str, color: str) -> None:
        """
        Add a way to the board.

        :param name: Name / Type of the way.
        :param color: Color of the way.
        """
        self.ways.append(Way(name, color))

    def distribute_city_tokens(
            self, tokens: list[CityToken], rng: random.Random
    ) -> None:
        """
        Shuffle the tokens of every letter and deal one to each matching city.

        :param tokens: Every city token of the game, 30 in total.
        :param rng: The random generator used to shuffle, kept injectable for
            tests.
        """
        by_letter: dict[str, list[CityToken]] = {}
        for token in tokens:
            by_letter.setdefault(token.roman_char, []).append(token)
        for letter, letter_tokens in by_letter.items():
            rng.shuffle(letter_tokens)
            cities_of_letter = [
                city for city in self.cities()
                if city is not self.capital and city.letter == letter
            ]
            for city, token in zip(cities_of_letter, letter_tokens):
                city.set_token(token)
                city.reveal()

    def neighbors(self, city: City) -> list[tuple[City, str]]:
        """List every city reachable from a city by a single route."""
        found = []
        for city_a, city_b, kind in self.routes:
            if city_a is city:
                found.append((city_b, kind))
            elif city_b is city:
                found.append((city_a, kind))
        return found

    def assign_bonus_markers(self) -> None:
        """Give every province the bonus marker of its most valuable good."""
        for province in self.provinces:
            best_good = province.most_valuable_good()
            if best_good is not None:
                province.set_bonus_marker(BonusMarker(best_good))

    def __repr__(self) -> str:
        return f"Board({self.map!r})"

    def get_routes(self) -> list[tuple[City, City, str]]:
        """Return every route of the board, as (city, city, kind) tuples."""
        return self.routes
