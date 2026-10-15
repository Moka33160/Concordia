"""
File: test_score_manager.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: Tests for the final scoring of the gods.
"""
from unittest.mock import MagicMock, patch

from concordia.managers.score_manager import ScoreManager
from concordia.models.card import Card, CardOrigin
from concordia.models.god import God
from concordia.models.resource import Good
from concordia.models.token import CityToken

CLOTH = Good("cloth", 7, "blue", 1, 5, ["brick", "cloth"])
BRICK = Good("brick", 3, "brown", 2, 1, ["food"])

JVPITER = God("JVPITER", "the sky", "1 VP per house", "...", 1)

BASES = {
    "calculate_vesta": 10,
    "calculate_jupiter": 20,
    "calculate_saturnus": 30,
    "calculate_mercurius": 40,
    "calculate_mars": 50,
}


def make_city(good, houses):
    city = MagicMock()
    city.token = CityToken("A", good) if good is not None else None
    city.houses = list(houses)
    return city


def make_player(color, hand=(), discarded=(), has_concordia=False):
    player = MagicMock()
    player.color = color
    player.hand = list(hand)
    player.discarded_cards = list(discarded)
    player.has_concordia = has_concordia
    return player


def make_manager(cities, players):
    game_state = MagicMock()
    game_state.players = players
    game_state.board.cities.return_value = cities
    game_state.get_player_by_color.side_effect = (
        lambda color: next(
            (p for p in players if p.color == color), None
        )
    )
    return ScoreManager(game_state)


def test_minerva_scores_the_matching_cities():
    cities = [
        make_city(CLOTH, ["red"]),
        make_city(CLOTH, ["red", "blue"]),
        make_city(CLOTH, ["blue"]),   # not the player's
        make_city(BRICK, ["red"]),    # wrong good
    ]
    player = make_player("red")
    manager = make_manager(cities, [player])

    assert manager.calculate_minerva("red", "cloth", 5) == 10


def score_with(cards, cities=(), has_concordia=False):
    """Score a player holding those cards."""
    player = make_player("red", hand=cards, has_concordia=has_concordia)
    manager = make_manager(list(cities), [player])

    with patch.multiple(
            ScoreManager,
            **{name: MagicMock(return_value=value)
               for name, value in BASES.items()}
    ):
        return manager.calculate_final_scores()["red"]


def test_every_roman_spelling_scores_its_god():
    spellings = {
        "VESTA": BASES["calculate_vesta"],
        "JVPITER": BASES["calculate_jupiter"],
        "SATVRNVS": BASES["calculate_saturnus"],
        "MERCVRIVS": BASES["calculate_mercurius"],
        "MARS": BASES["calculate_mars"],
    }
    for name, expected in spellings.items():
        god = God(name, "...", "...", "...", 1)
        card = Card("A CARD", god, "...", CardOrigin.MARKET)
        assert score_with([card]) == expected, name


def test_concordia_is_worth_seven():
    assert score_with([], has_concordia=True) == 7
