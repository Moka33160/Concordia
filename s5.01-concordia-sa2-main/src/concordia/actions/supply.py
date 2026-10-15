"""
File: supply.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Gives the produced goods to a player, and asks what to drop when
             the storehouse is full.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from concordia.actions.requests import ChooseGood, Flow

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.models.player import Player


def store_units(player: Player, good: str, amount: int = 1) -> int:
    """
    Put units of one good into a storehouse, as many as there is room for.

    :param player: The player receiving the goods.
    :param good: The name of the good produced.
    :param amount: How many units are produced.
    :return: How many units were actually stored.
    """
    stored = 0

    for _ in range(amount):
        if not player.give_good_to_player(good):
            break
        stored += 1

    return stored


def receive_goods(ctx: ActionContext, units: Iterable[str]) -> Flow:
    """
    Hand a batch of produced units to the player playing the card.

    :param ctx: The card, the player and the game.
    :param units: The good names produced, one entry per unit.
    :return: How many units were stored.
    """
    player = ctx.player
    incoming = list(units)
    free = player.get_goods_storehouse_capacity()

    if free <= 0 or not incoming:
        return 0

    if free >= len(incoming):
        for good in incoming:
            player.give_good_to_player(good)
        return len(incoming)

    stored = 0

    while stored < free and incoming:
        offered = tuple(sorted(set(incoming)))

        if len(offered) == 1:
            good = offered[0]
        else:
            good = yield ChooseGood(
                f"Only {free - stored} storage space(s) left: "
                f"which good do you take?",
                options=offered,
            )

        incoming.remove(good)
        player.give_good_to_player(good)
        stored += 1

    return stored


def give_goods(ctx: ActionContext, good: str, amount: int) -> Flow:
    """
    Hand several units of one good to the player playing the card.

    :param ctx: The card, the player and the game.
    :param good: The name of the good produced.
    :param amount: How many units are produced.
    :return: How many units were stored.
    """
    return (yield from receive_goods(ctx, [good] * amount))
