"""
File: test_colonist.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the COLONIST action: take the sestertii or place a
             colonist.
"""
from unittest.mock import MagicMock

from concordia.actions import colonist
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.player import AIPlayer
from tests.actions.flows import named, option, run

TAKE = option("sestertii")
PLACE = option("place")


def create_player(color="red", food=5, tool=5, ways=("land", "sea")):
    """
    A player with a full storehouse and a colonist of each way in
    reserve.
    """
    player = AIPlayer(color)
    player.fill_storehouse(
        [Colonist(way) for way in ways], {"food": food, "tool": tool}
    )
    return player


def create_city(name, houses=None):
    """A city of the board, with the houses already built in it."""
    city = City(name, "A", 3)
    city.houses = list(houses or [])
    return city


def create_ctx(player, capital, cities=()):
    """That player playing COLONIST on a one-province board."""
    province = MagicMock()
    province.cities = list(cities)

    game_state = MagicMock()
    game_state.board.capital = capital
    game_state.board.provinces = [province]

    card = Card("COLONIST", None, "colonist action", CardOrigin.MARKET,
                deck_number=2)
    return ActionContext(card, player, game_state)


def test_take_sestertii():
    player = create_player()
    capital = create_city("Roma")
    player.place_colonist("land", capital)
    player.place_colonist("sea", capital)

    result, script = run(
        colonist.play(create_ctx(player, capital)), TAKE
    )

    assert result is True
    assert player.sestertii == 7
    assert script.asked == ["ChooseOption"]


def test_place_colonist_in_the_capital():
    player = create_player()
    capital = create_city("Roma")

    result, script = run(
        colonist.play(create_ctx(player, capital)),
        PLACE, "land", named("Roma"), None,
    )

    assert result is True
    assert script.asked == [
        "ChooseOption", "ChooseWay", "ChooseCity", "ChooseWay",
    ]
    assert [c.city for c in player.colonists] == [capital]
    assert capital.colonists == player.colonists


def test_place_colonist_costs_food_and_tool():
    player = create_player(food=2, tool=2)
    capital = create_city("Roma")

    run(colonist.play(create_ctx(player, capital)), PLACE, "land",
        named("Roma"), None)

    assert player.storehouse == {"food": 1, "tool": 1}


def test_place_several_colonists():
    """
    The rules allow several colonists in one turn, one food and one tool
    each.
    """
    player = create_player(food=2, tool=3, ways=("land", "sea"))
    capital = create_city("Roma")

    result, _script = run(
        colonist.play(create_ctx(player, capital)),
        PLACE, "land", named("Roma"), "sea", named("Roma"),
    )

    assert result is True
    assert [c.way for c in player.colonists] == ["land", "sea"]
    assert player.storehouse == {"food": 0, "tool": 1}
