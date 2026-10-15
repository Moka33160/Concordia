"""
File: test_diplomat.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the DIPLOMAT action, which copies an opponent's last
             card.
"""
from unittest.mock import MagicMock

from concordia.actions import diplomat
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.player import AIPlayer
from tests.actions.flows import first, run


def make_card(name, origin=CardOrigin.STARTING):
    """A card of that name."""
    return Card(name, None, f"{name} action", origin)


def make_ctx(player, *others):
    """That player playing DIPLOMAT at a table with those opponents."""
    game_state = MagicMock()
    game_state.players = [player, *others]

    return ActionContext(make_card("DIPLOMAT"), player, game_state)


def with_discard(color, *card_names):
    """An opponent whose discard pile ends on those cards."""
    player = AIPlayer(color)
    player.discarded_cards = [make_card(name) for name in card_names]
    return player


def test_is_playable_with_an_opponent_card():
    player = AIPlayer("red")
    ctx = make_ctx(player, with_discard("blue", "TRIBUNE"))

    assert diplomat.is_playable(ctx) is True


def test_only_the_top_card_is_offered():
    player = AIPlayer("red")
    rival = with_discard("blue", "TRIBUNE", "PREFECT")
    ctx = make_ctx(player, rival)

    offered = diplomat.copyable_cards(ctx)

    assert [card.name for _owner, card in offered] == ["PREFECT"]


def test_diplomat_copies_the_action():
    player = AIPlayer("red")
    rival = with_discard("blue", "TRIBUNE")
    ctx = make_ctx(player, rival)
    player.discarded_cards = [make_card("PREFECT"), make_card("SENATOR")]

    result, script = run(diplomat.play(ctx), first)

    assert result is True
    assert script.asked[0] == "ChooseDiscardCard"
    # The TRIBUNE took the player's own two discards back into hand.
    assert [card.name for card in player.hand] == ["PREFECT", "SENATOR"]
    assert player.discarded_cards == []
