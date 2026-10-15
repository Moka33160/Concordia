"""
File: test_market.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the card market and its display.
"""
import random

from concordia.models.card import Card, CardOrigin
from concordia.models.market import CardMarket


def make_market(cards_per_deck=3, decks=5):
    market = CardMarket()
    for deck_number in range(1, decks + 1):
        for copy in range(cards_per_deck):
            name = f"CARD-{deck_number}-{copy}"
            market.add_card(
                Card(name, "GOD", "...", CardOrigin.MARKET, deck_number)
            )
    return market


def test_prepare_stack_drops_the_unused_decks():
    market = make_market()

    market.prepare_stack(nb_players=2, rng=random.Random(1))

    deck_numbers = {card.deck_number for card in market.stack + market.display}
    assert deck_numbers == {1, 2}


def test_prepare_stack_displays_seven_cards():
    market = make_market()

    market.prepare_stack(nb_players=5, rng=random.Random(1))

    assert len(market.display) == 7


def test_draw_takes_the_top_cards():
    market = make_market(cards_per_deck=10, decks=1)
    market.prepare_stack(nb_players=1, rng=random.Random(1))
    remaining = len(market.stack)

    drawn = market.draw(1)

    assert len(drawn) == 1
    assert len(market.stack) == remaining - 1
