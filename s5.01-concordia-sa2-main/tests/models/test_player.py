"""
File: test_player.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the Player classes.
"""
import random

import pytest

from concordia.models.card import Card, CardOrigin
from concordia.models.player import AIPlayer, Player


def test_player_is_abstract():
    with pytest.raises(TypeError):
        Player("red")


def test_ai_chooses_a_card_from_its_hand():
    hand = [
        Card("TRIBUNE", "MARS", "...", CardOrigin.STARTING),
        Card("SENATOR", "VESTA", "...", CardOrigin.STARTING),
    ]
    player = AIPlayer("red", rng=random.Random(1))

    chosen = player.choose_card(hand)

    assert chosen in hand


def test_fill_storehouse_adds_up_the_goods():
    player = AIPlayer("red")

    player.fill_storehouse([], {"food": 2})
    player.fill_storehouse([], {"food": 1, "brick": 1})

    assert player.storehouse == {"food": 3, "brick": 1}


def test_praefectus_magnus_is_held_as_a_card():
    player = AIPlayer("red")
    card = Card("PRÆFECTVS MAGNVS", None, "...", CardOrigin.AWARD)

    player.give_praefectus_magnus(card)

    assert player.has_praefectus_magnus is True
    assert player.praefectus_magnus is card
