"""
File: specialist.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The MINERVA specialists (MASON, FARMER, SMITH, VINTNER, WEAVER),
             which produce one good per matching city.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import Flow
from concordia.actions.supply import give_goods
from concordia.models.city import City

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext


def is_playable(ctx: ActionContext) -> bool:
    """Whether the specialist can be played."""
    return True


def play(ctx: ActionContext) -> Flow:
    """
    Produce one good per city of the specialist's kind the player lives in.
    """
    good = ctx.card.good

    if good is not None:
        cities: list[City] = ctx.game_state.board.cities()
        yield from give_goods(ctx, good.name, get_nb_value(ctx, cities))

    return True


def get_nb_value(ctx: ActionContext, cities: list[City]) -> int:
    """
    Count the cities producing the specialist's good the player has a house
    in.

    :param ctx: The context of the action.
    :param cities: The cities of the board.
    :return: How many goods the specialist produces.
    """
    good = ctx.card.good
    if good is None:
        return 0

    return sum(
        1
        for city in cities
        if city.token is not None
        and city.token.good is not None
        and city.token.good.name == good.name
        and ctx.player.color in city.houses
    )
