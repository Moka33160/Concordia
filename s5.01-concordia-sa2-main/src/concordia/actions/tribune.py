"""
File: tribune.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The TRIBUNE action: take the whole discard pile back into hand,
             cash one sestertius for every card past the third, and buy one
             colonist for the capital if the storehouse can pay for it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import ChooseWay, Confirm, Flow
from concordia.rules import COLONIST_COST

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.models.card import Card


def is_playable(ctx: ActionContext) -> bool:
    """Whether the tribune can be played."""
    return True


def play(ctx: ActionContext) -> Flow:
    """Take the discard pile back, cash it in, and offer a colonist."""
    played_cards = get_all_played_cards(ctx)
    add_played_cards(ctx, played_cards)
    clear_discard(ctx)
    calculate_sestertii(ctx, played_cards)
    score_intermediate(ctx)

    if can_purchase_colonist(ctx):
        if (yield Confirm("Buy a colonist for the capital?")):
            way = yield ChooseWay(
                "Which colonist do you buy?",
                options=tuple(available_colonist_ways(ctx)),
            )
            purchase_colonist(ctx, way)

    return True


def get_all_played_cards(ctx: ActionContext) -> list[Card]:
    """Return all cards played by the player."""
    return ctx.player.discarded_cards


def clear_discard(ctx: ActionContext) -> None:
    """Clear the discard pile of the player."""
    ctx.player.discarded_cards = []


def add_played_cards(ctx: ActionContext, cards: list[Card]) -> None:
    """
    Add the cards played by the player to his hand.

    :param ctx: The card, the player and the game.
    :param cards: A list of cards to add to the player hand.
    """
    for card in cards:
        ctx.player.add_to_hand(card)


def calculate_sestertii(ctx: ActionContext, cards: list[Card]) -> None:
    """
    Calculate the amount given to the player.

    :param ctx: The card, the player and the game.
    :param cards: A list of cards used to calculate the number of sestertii
        earned.
    """
    ctx.player.receive_sestertii(max(len(cards) - 3, 0))


def score_intermediate(ctx: ActionContext) -> None:
    """Give the player their intermediate scoring, the first TRIBUNE only."""
    game = ctx.game_state

    # Compared to True so a mocked game state does not switch the scoring on.
    if getattr(game, "intermediate_scoring", False) is not True:
        return

    if ctx.player.has_scored_intermediate:
        return

    # Imported here to avoid a circular import with the registry.
    from concordia.managers.score_manager import ScoreManager

    scores = ScoreManager(game)
    scores.intermediate_score(ctx.player)
    scores.close_intermediate_scoring()


def can_purchase_colonist(ctx: ActionContext) -> bool:
    """Checks whether a player can purchase a colonist."""
    inventory = ctx.player.storehouse

    return (
        bool(ctx.player.storehouse_colonists)
        and all(inventory.get(good, 0) > 0 for good in COLONIST_COST)
    )


def available_colonist_ways(ctx: ActionContext) -> list[str]:
    """The ways the player still has a colonist in reserve for."""
    reserve = {colonist.way for colonist in ctx.player.storehouse_colonists}

    return [way.name for way in ctx.game_state.board.ways
            if way.name in reserve]


def purchase_colonist(ctx: ActionContext, way: str) -> bool:
    """
    Purchase a colonist for the player and place it on the capital.

    :param ctx: The card, the player and the game.
    :param way: the type of colonist the player want to purchase.
    :return: True when a colonist was bought and placed.
    """
    placed = ctx.player.place_colonist(way, ctx.game_state.board.capital)

    if placed is None:
        return False

    for good in COLONIST_COST:
        ctx.player.storehouse[good] -= 1

    return True
