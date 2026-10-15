"""
File: test_architect.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the ARCHITECT action: moving the colonists, then
             building.
"""
from unittest.mock import MagicMock

from concordia.actions import architect
from concordia.actions.context import ActionContext
from concordia.models.board import Board
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from concordia.models.token import CityToken
from tests.actions.flows import first, run, stop_after

# A brick city: 1 sestertius a house, paid with one brick and one food.
BRICK = Good("brick", 3, "#8b5a2b", 2, 1, ["brick", "food"])


def make_city(name, good=BRICK, houses=(), nb_house_max=3):
    """A city with a revealed token and the houses already built."""
    city = City(name, "A", nb_house_max)
    if good is not None:
        city.set_token(CityToken("A", good))
    city.houses = list(houses)
    return city


def make_board(cities=(), routes=()):
    """A board with those cities and routes, the first one the capital."""
    board = Board("Test")

    for index, city in enumerate(cities):
        if index == 0:
            board.set_capital(city)
        else:
            board.index_city(city)

    for city_a, city_b, kind in routes:
        board.add_route(city_a.name, city_b.name, kind)

    return board


def make_ctx(player, board):
    """That player playing ARCHITECT on that board."""
    game_state = MagicMock()
    game_state.board = board

    card = Card("ARCHITECT", None, "...", CardOrigin.STARTING)
    return ActionContext(card, player, game_state)


def make_player(color="red", sestertii=0, goods=None, houses=15):
    """A player with a purse, a storehouse and a supply of houses."""
    player = AIPlayer(color)
    player.sestertii = sestertii
    player.init_supply(houses)
    player.fill_storehouse(
        [Colonist(way) for way in ("land", "sea") for _ in range(3)],
        dict(goods or {}),
    )
    return player


def line(kind="land"):
    """The small map used by most of the tests: ROMA - OSTIA - PISAE."""
    roma = make_city("Roma")
    ostia = make_city("Ostia")
    pisae = make_city("Pisae")
    board = make_board(
        (roma, ostia, pisae),
        ((roma, ostia, kind), (ostia, pisae, kind)),
    )
    return board, roma, ostia, pisae


def route_between(board, city_a, city_b, kind="land"):
    """The one route of that kind joining two cities."""
    for route in board.routes:
        if route.kind == kind and route.touches(city_a) \
                and route.touches(city_b):
            return route
    raise AssertionError(f"no {kind} route between {city_a} and {city_b}")


def take(name):
    """Answer a route request with the route reaching a named city."""
    def pick(request):
        for route in request.options:
            if any(city.name == name for city in route.cities):
                return route
        raise AssertionError(
            f"no route to {name!r} was offered: {list(request.options)}"
        )

    return pick


def city(name):
    """Answer a city request with the city of that name."""
    def pick(request):
        for choice in request.options:
            if choice.name == name:
                return choice
        raise AssertionError(
            f"{name!r} was not offered: {list(request.options)}"
        )

    return pick


def test_is_playable_with_a_colonist_on_the_board():
    board, roma, _ostia, _pisae = line()
    player = make_player()
    player.place_colonist("land", roma)

    assert architect.is_playable(make_ctx(player, board)) is True


def test_is_not_playable_without_colonist():
    board, _roma, _ostia, _pisae = line()
    player = make_player()
    player.fill_storehouse([Colonist("land")], {})

    assert architect.is_playable(make_ctx(player, board)) is False


def test_colonist_leaves_the_city_for_a_route():
    board, roma, ostia, _pisae = line()
    player = make_player()
    colonist = player.place_colonist("land", roma)
    road = route_between(board, roma, ostia)

    result, script = run(
        architect.play(make_ctx(player, board)),
        first, take("Ostia"), None,
    )

    assert result is True
    assert script.asked[:2] == ["ChooseColonist", "ChooseRoute"]
    assert colonist.route is road
    assert colonist.city is None
    assert roma.colonists == []
    assert road.colonists == [colonist]


def test_building_pays_the_cost():
    board, roma, ostia, _pisae = line()
    player = make_player(sestertii=10, goods={"brick": 2, "food": 2})
    player.place_colonist("land", roma)

    run(
        architect.play(make_ctx(player, board)),
        first, take("Ostia"), city("Ostia"), None,
    )

    # A first house in a brick city: 1 sestertius, one brick and one food.
    assert ostia.houses == ["red"]
    assert player.sestertii == 9
    assert player.storehouse == {"brick": 1, "food": 1}
    assert player.houses == 14


def test_occupied_route_is_not_offered():
    board, roma, ostia, _pisae = line()
    blocked = route_between(board, roma, ostia)
    other = make_player("blue")
    other.place_colonist("land", roma).place(blocked)
    player = make_player()
    colonist = player.place_colonist("land", roma)

    assert architect.is_free(blocked) is False
    assert architect.destinations(make_ctx(player, board), colonist) == {}


def test_cancel_puts_the_colonist_back():
    """Cancelling the card undoes the moves already made."""
    board, roma, ostia, _pisae = line()
    player = make_player()
    colonist = player.place_colonist("land", roma)
    player.place_colonist("land", roma)
    road = route_between(board, roma, ostia)

    stop_after(
        architect.play(make_ctx(player, board)),
        lambda request: colonist, take("Ostia"),
    )

    assert colonist.position is roma
    assert road.colonists == []
    assert colonist in roma.colonists
