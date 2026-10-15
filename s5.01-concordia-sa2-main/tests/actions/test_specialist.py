"""
File: test_specialist.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the MINERVA specialist cards, which produce one good.
"""
from unittest.mock import MagicMock

from concordia.actions import specialist
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from concordia.models.token import CityToken
from tests.actions.flows import run

CLOTH = Good("cloth", 7, "#3b5f9e", 1, 5)
BRICK = Good("brick", 3, "#8b5a2b", 2, 1)


def make_city(good, houses=()):
    """A city with a revealed token and the houses already built."""
    city = City("Aquileia", "A", 3)
    city.set_token(CityToken("A", good))
    city.houses = list(houses)
    return city


def make_ctx(player, cities, good=CLOTH, card_name="WEAVER"):
    """That player playing a specialist on a board of those cities."""
    game_state = MagicMock()
    game_state.board.cities.return_value = list(cities)

    card = Card(card_name, None, "...", CardOrigin.MARKET, deck_number=2,
                good=good)
    return ActionContext(card, player, game_state)


def test_specialist_produces_one_good_per_city():
    player = AIPlayer("red")
    cities = [
        make_city(CLOTH, houses=["red"]),
        make_city(CLOTH, houses=["red", "blue"]),
        make_city(CLOTH, houses=["blue"]),
    ]

    result, script = run(specialist.play(make_ctx(player, cities)))

    assert result is True
    assert player.storehouse == {"cloth": 2}
    assert script.requests == []


def test_specialist_ignores_the_other_goods():
    player = AIPlayer("red")
    cities = [make_city(BRICK, houses=["red"]), make_city(CLOTH,
                                                          houses=["red"])]

    run(specialist.play(make_ctx(player, cities)))

    assert player.storehouse == {"cloth": 1}


def test_full_storehouse_produces_nothing():
    """
    A full storehouse takes nothing in, and no good is discarded to make
    room.
    """
    player = AIPlayer("red")
    player.fill_storehouse([], {"brick": 12})
    cities = [make_city(CLOTH, houses=["red"])]

    _result, script = run(specialist.play(make_ctx(player, cities)))

    assert script.asked == []
    assert player.storehouse == {"brick": 12}
