"""
File: test_card_manager.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the CardManager, which sends a card to its action.
"""
from unittest.mock import MagicMock

from concordia import actions
from concordia.managers.card_manager import CardManager
from concordia.models.card import Card, CardOrigin
from concordia.models.god import God
from concordia.models.player import AIPlayer

MARS = God("MARS", "war", "2 VP per colonist", "...", 2)

# A card name no action is registered for.
UNKNOWN = "CONCORDIA"


def make_manager():
    """A manager over a mocked game."""
    return CardManager(MagicMock())


def test_unknown_card_has_no_flow():
    card = Card(UNKNOWN, MARS, "...", CardOrigin.AWARD)

    assert make_manager().flow(card, AIPlayer("red")) is None


def test_play_calls_the_registered_action(monkeypatch):
    game_state = MagicMock()
    manager = CardManager(game_state)
    card = Card("FAKE", None, "...", CardOrigin.STARTING)
    player = AIPlayer("red")
    seen = {}

    def fake_action(ctx):
        seen["ctx"] = ctx
        return True
        yield  # pragma: no cover - never reached, makes this a generator

    monkeypatch.setitem(actions.ACTIONS, "FAKE", fake_action)

    assert manager.play(card, player, lambda request: None) is True
    assert seen["ctx"].card is card
    assert seen["ctx"].player is player
    assert seen["ctx"].game_state is game_state


def test_played_card_leaves_the_hand():
    card = Card("PREFECT", MARS, "...", CardOrigin.STARTING)
    player = AIPlayer("red")
    player.hand.append(card)

    make_manager().lay_down(card, player)

    assert card not in player.hand
    assert player.discarded_cards == [card]
