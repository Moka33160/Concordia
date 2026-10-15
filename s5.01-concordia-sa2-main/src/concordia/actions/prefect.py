"""
File: prefect.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The PREFECT action: produce in a province and turn its marker
             over, or collect the turned markers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import (
    ChooseOption, ChooseProvince, Flow, Option,
)
from concordia.actions.supply import give_goods, receive_goods, store_units
from concordia.models.province import Province

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext

PRODUCE = Option("produce", "Produce in a province")
COLLECT = Option("collect", "Collect the sestertii of the turned provinces")


def is_playable(ctx: ActionContext) -> bool:
    """Whether the prefect has anything to act on."""
    return bool(get_active_provinces(ctx) or get_flipped_provinces(ctx))


def play(ctx: ActionContext) -> Flow:
    """Produce in a province, or collect what the turned markers are worth."""
    choices = tuple(
        option for option, available in (
            (PRODUCE, get_active_provinces(ctx)),
            (COLLECT, get_flipped_provinces(ctx)),
        ) if available
    )

    if not choices:
        return False

    chosen = yield ChooseOption(
        "What does the Prefect do?", options=choices,
    )

    if chosen is COLLECT:
        collect_sestertii(ctx)
        return True

    province = yield ChooseProvince(
        "Produce in which province?",
        options=tuple(get_active_provinces(ctx)),
    )
    yield from produce_in_province(ctx, province)
    return True


def get_active_provinces(ctx: ActionContext) -> list[Province]:
    """The provinces whose marker is still face up, and can be produced in."""
    return [
        province for province in ctx.game_state.board.provinces
        if not province.is_flipped
    ]


def get_flipped_provinces(ctx: ActionContext) -> list[Province]:
    """The provinces whose marker is turned to its coin side."""
    return [
        province for province in ctx.game_state.board.provinces
        if province.is_flipped
    ]


def produce_in_province(ctx: ActionContext, province: Province) -> Flow:
    """
    Take the province's bonus, turn its marker over, then let it produce.

    :param ctx: The card, the player and the game.
    :param province: The province produced in.
    """
    before = table_before(ctx, province)

    try:
        yield from give_bonus(ctx, province)
        province.is_flipped = True

        harvest: dict[object, list[str]] = {}

        for city in province.cities:
            if city.token is None or city.token.good is None:
                continue

            good_name = city.token.good.name

            for house_color in city.houses:
                owner = ctx.game_state.get_player_by_color(house_color)

                if owner is not None:
                    harvest.setdefault(owner, []).append(good_name)

        for owner, units in harvest.items():
            if owner is ctx.player:
                yield from receive_goods(ctx, units)
            else:
                for good_name in units:
                    store_units(owner, good_name)
    except GeneratorExit:
        put_back(before)
        raise


def table_before(ctx: ActionContext, province: Province) -> dict:
    """
    Note everything producing can change, before it changes anything.

    :param ctx: The card, the player and the game.
    :param province: The province about to be produced in.
    :return: What `put_back` needs to undo the production.
    """
    seats = ctx.game_state.players

    return {
        "province": province,
        "flipped": province.is_flipped,
        "storehouses": {
            seat: dict(seat.storehouse) for seat in seats
        },
        "flag": {
            seat: (seat.has_praefectus_magnus, seat.praefectus_magnus)
            for seat in seats
        },
    }


def put_back(before: dict) -> None:
    """Put the game back to what `table_before` noted down."""
    before["province"].is_flipped = before["flipped"]

    for seat, storehouse in before["storehouses"].items():
        seat.storehouse.clear()
        seat.storehouse.update(storehouse)

    for seat, (has_flag, card) in before["flag"].items():
        seat.has_praefectus_magnus = has_flag
        seat.praefectus_magnus = card


def give_bonus(ctx: ActionContext, province: Province) -> Flow:
    """
    Hand the province's bonus marker to the player who produced.

    :param ctx: The card, the player and the game.
    :param province: The province produced in.
    """
    marker = province.bonus_marker

    if marker is None:
        return

    amount = 2 if ctx.player.has_praefectus_magnus else 1
    yield from give_goods(ctx, marker.good.name, amount)

    if ctx.player.has_praefectus_magnus:
        ctx.game_state.pass_praefectus_magnus(ctx.player)


def collect_sestertii(ctx: ActionContext) -> None:
    """Cash in every turned marker and set them all back face up."""
    total_cash = 0

    for province in get_flipped_provinces(ctx):
        marker = province.bonus_marker

        if marker is not None:
            total_cash += marker.sestertii

        province.is_flipped = False

    ctx.player.receive_sestertii(total_cash)
