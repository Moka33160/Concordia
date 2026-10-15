"""
File: mercator.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The MERCATOR action: take the sestertii of the card, then trade
             twice.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import (
    ChooseAmount, ChooseGood, ChooseOption, Flow, Option,
)
from concordia.actions.supply import give_goods
from concordia.models.card import CardOrigin

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.models.resource import Good

BUY = Option("buy", "Buy a good")
SELL = Option("sell", "Sell a good")

# How many types of goods can be traded, and what each card pays out.
TRADE_TYPES = 2
STARTING_SESTERTII = 3
MARKET_SESTERTII = 5


def is_playable(ctx: ActionContext) -> bool:
    """Whether the mercator can be played."""
    return True


def play(ctx: ActionContext) -> Flow:
    """Pay the player out, then let them trade in up to two types of goods."""
    give_sestertii(ctx)

    traded: set[str] = set()

    for _ in range(TRADE_TYPES):
        good = yield from trade(ctx, traded)

        if good is not None:
            traded.add(good)

    return True


def give_sestertii(ctx: ActionContext) -> None:
    """Give sestertii to the player depending on the type of card."""
    ctx.player.receive_sestertii(
        STARTING_SESTERTII if ctx.card.origin == CardOrigin.STARTING
        else MARKET_SESTERTII
    )


def trade(ctx: ActionContext, traded: set[str]) -> Flow:
    """
    Buy or sell one kind of good, or pass the trade by.

    :param ctx: The card, the player and the game.
    :param traded: The good names already traded this turn, which are no
        longer on offer.
    :return: The name of the good traded, None when the player passed or had
        nothing left to trade.
    """
    choices = tuple(
        option for option, available in (
            (BUY, buyable_goods(ctx, traded)),
            (SELL, sellable_goods(ctx, traded)),
        ) if available
    )

    if not choices:
        return None

    chosen = yield ChooseOption(
        "Buy or sell?", options=choices, optional=True,
    )

    if chosen is None:
        return None

    buying = chosen is BUY
    goods = (
        buyable_goods(ctx, traded) if buying else sellable_goods(ctx, traded)
    )

    good = yield ChooseGood(
        f"Which good do you {chosen.key}?",
        options=tuple(good.name for good in goods),
        optional=True, giving_up=not buying,
    )

    if good is None:
        return None

    known = ctx.game_state.goods_by_name[good]
    most = max_buyable(ctx, known) if buying else max_sellable(ctx, known)

    amount = yield ChooseAmount(
        f"How many {good} do you {chosen.key}?", minimum=1, maximum=most,
    )

    if buying:
        yield from buy_good(ctx, known, amount)
    else:
        sell_good(ctx, known, amount)

    return good


def max_buyable(ctx: ActionContext, good: Good) -> int:
    """
    How many units of a good the player may buy.

    :param ctx: The card, the player and the game.
    :param good: The good being bought.
    :return: The largest number of units the player can take in.
    """
    return min(
        ctx.player.sestertii // good.value,
        ctx.player.get_goods_storehouse_capacity(),
    )


def max_sellable(ctx: ActionContext, good: Good) -> int:
    """
    How many units of a good the storehouse holds.

    :param ctx: The card, the player and the game.
    :param good: The good being sold.
    :return: The largest number of units the player can part with.
    """
    return ctx.player.storehouse.get(good.name, 0)


def buyable_goods(ctx: ActionContext,
                  traded: set[str] | None = None) -> list[Good]:
    """
    The goods the player can afford and has room for.

    :param ctx: The card, the player and the game.
    :param traded: The good names already traded this turn, left out.
    :return: The goods within reach of the purse and the storehouse.
    """
    traded = traded or set()

    return [
        good for good in ctx.game_state.goods_by_name.values()
        if good.name not in traded and max_buyable(ctx, good) >= 1
    ]


def sellable_goods(ctx: ActionContext,
                   traded: set[str] | None = None) -> list[Good]:
    """
    The goods the player holds at least one unit of.

    :param ctx: The card, the player and the game.
    :param traded: The good names already traded this turn, left out.
    :return: The goods the storehouse can part with.
    """
    traded = traded or set()

    return [
        good for good in ctx.game_state.goods_by_name.values()
        if good.name not in traded and max_sellable(ctx, good) >= 1
    ]


def sell_good(ctx: ActionContext, good: Good, nb: int) -> None:
    """
    Sell a quantity of a good, out of the storehouse and into the purse.

    :param ctx: The card, the player and the game.
    :param good: The good to sell.
    :param nb: The number of units to sell.
    """
    ctx.player.storehouse[good.name] -= nb
    ctx.player.receive_sestertii(good.value * nb)


def buy_good(ctx: ActionContext, good: Good, nb: int) -> Flow:
    """
    Buy a quantity of a good, out of the purse and into the storehouse.

    :param ctx: The card, the player and the game.
    :param good: The good to buy.
    :param nb: The number of units to buy.
    """
    bought = yield from give_goods(ctx, good.name, nb)
    ctx.player.sestertii -= good.value * bought
