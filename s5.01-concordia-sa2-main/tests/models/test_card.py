"""
File: test_card.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 08-09-2026
Description: Tests for the Card model.
"""
from concordia.models.card import Card, CardOrigin
from concordia.models.god import God
from concordia.models.resource import Good

BRICK = Good("brick", 3, "brown", 2, 1)
CLOTH = Good("cloth", 7, "blue", 1, 5)
MARS = God("MARS", "war", "2 VP per colonist", "...", 2)


def test_starting_card_has_no_deck_or_cost():
    card = Card("MERCATOR", None, "mercator action", CardOrigin.STARTING)

    assert card.name == "MERCATOR"
    assert card.god is None
    assert card.text == "mercator action"
    assert card.origin is CardOrigin.STARTING
    assert card.deck_number is None
    assert card.good is None
    assert card.cost == []


def test_market_card_keeps_its_deck_and_cost():
    card = Card("MERCATOR", MARS, "mercator action", CardOrigin.MARKET,
                deck_number=2, good=CLOTH, cost=[BRICK, CLOTH])

    assert card.origin is CardOrigin.MARKET
    assert card.god is MARS
    assert card.deck_number == 2
    assert card.good is CLOTH
    assert [good.name for good in card.cost] == ["brick", "cloth"]
