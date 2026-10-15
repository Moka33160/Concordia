"""
File: diplomat.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The DIPLOMAT action: play again the card on top of an opponent's
             discard pile.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import ChooseDiscardCard, Flow

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.models.card import Card
    from concordia.models.player import Player


def is_playable(ctx: ActionContext) -> bool:
    """Whether there is an opponent's card worth copying."""
    return bool(copyable_cards(ctx))


def play(ctx: ActionContext) -> Flow:
    """Run the action of a card sitting on an opponent's discard pile."""
    # Imported here to avoid a circular import with the registry.
    from concordia.actions import ACTIONS

    options = tuple(copyable_cards(ctx))

    if not options:
        return False

    chosen = yield ChooseDiscardCard(
        "Copy the last card played by which opponent?", options=options,
    )
    _owner, target = chosen

    return (yield from ACTIONS[target.name](ctx.for_card(target)))


def copyable_cards(ctx: ActionContext) -> list[tuple[Player, Card]]:
    """The top discarded card of every opponent the diplomat could copy."""
    from concordia.actions import ACTIONS

    return [
        (player, player.discarded_cards[-1])
        for player in ctx.game_state.players
        if player is not ctx.player
        and player.discarded_cards
        and player.discarded_cards[-1].name in ACTIONS
        and player.discarded_cards[-1].name != "DIPLOMAT"
    ]
