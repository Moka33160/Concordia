"""
File: senator.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The SENATOR action: buy up to two cards of the display, then slide
             the stack up.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import ChooseGood, ChooseMarketCard, Flow

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.models.card import Card

MAX_PURCHASES = 2


def play(ctx: ActionContext) -> Flow:
    """Buy up to two cards of the display, one after the other."""
    return (yield from purchase_cards(ctx, MAX_PURCHASES))


def purchase_cards(ctx: ActionContext, max_purchases: int,
                   slot_surcharge: bool = True) -> Flow:
    """
    Buy cards of the display, one after the other.

    :param ctx: The card, the player and the game.
    :param max_purchases: How many cards the played card allows. The display
        is only slid up once every purchase is over, as the rules say "after
        the purchase(s)", so a card bought and then given up stays in the
        display.
    :param slot_surcharge: Whether the goods of the display slot are due on
        top of the card price, which only the SENATOR pays.
    :return: True when the action was carried out, False when there is nothing
        the player could ever buy.
    """
    if not affordable_cards(ctx, slot_surcharge):
        return False

    before = purse_before(ctx)
    bought: list[Card] = []

    try:
        for remaining in range(max_purchases, 0, -1):
            choices = [
                card for card in affordable_cards(ctx, slot_surcharge)
                if card not in bought
            ]

            if not choices:
                break

            card = yield ChooseMarketCard(
                f"Buy which card? ({remaining} left to buy)",
                options=tuple(choices), optional=True,
            )

            if card is None:
                break

            yield from buy(ctx, card, slot_surcharge)
            bought.append(card)
    except GeneratorExit:
        put_back(ctx, before)
        raise

    take_out_and_refill(ctx, bought)

    return True


# --- Prices ---

def card_cost(card: Card) -> dict[str, int]:
    """The price of a card, as how many units of each good it takes."""
    cost: dict[str, int] = {}

    for good in card.cost:
        cost[good.name] = cost.get(good.name, 0) + 1

    return cost


def slot_cost(ctx: ActionContext, card: Card,
              slot_surcharge: bool = True) -> dict[str, int]:
    """
    The named goods the display slot of a card asks for on top of it.

    :param ctx: The card, the player and the game.
    :param card: The card being priced.
    :param slot_surcharge: Whether the slot is paid for at all.
    :return: How many units of each good the slot costs, keyed by good name,
        empty when the slot asks for no named good.
    """
    if not slot_surcharge:
        return {}

    slot = ctx.game_state.market.slot_from(card)

    if slot is None or slot.good is None:
        return {}

    return {slot.good: slot.n_goods or 1}


def any_good_cost(ctx: ActionContext, card: Card,
                  slot_surcharge: bool = True) -> int:
    """
    How many goods of the buyer's choice the display slot of a card asks for,
    on top of the named ones.

    :param ctx: The card, the player and the game.
    :param card: The card being priced.
    :param slot_surcharge: Whether the slot is paid for at all.
    :return: 1 when the slot asks for a good of the buyer's choice, 0
        otherwise.
    """
    if not slot_surcharge:
        return 0

    slot = ctx.game_state.market.slot_from(card)

    return 1 if slot is not None and slot.any_good_required else 0


def total_cost(ctx: ActionContext, card: Card,
               slot_surcharge: bool = True) -> dict[str, int]:
    """
    The named goods a card costs: its own price and its slot surcharge.

    :param ctx: The card, the player and the game.
    :param card: The card being priced.
    :param slot_surcharge: Whether the slot is paid for on top of the card.
    :return: How many units of each good the purchase costs, keyed by good
        name.
    """
    cost = card_cost(card)

    for good, quantity in slot_cost(ctx, card, slot_surcharge).items():
        cost[good] = cost.get(good, 0) + quantity

    return cost


def can_purchase(ctx: ActionContext, card: Card,
                 slot_surcharge: bool = True) -> bool:
    """
    Whether the storehouse holds enough goods to pay for a card.

    :param ctx: The card, the player and the game.
    :param card: The card the player is looking at.
    :param slot_surcharge: Whether the slot is paid for on top of the card.
    :return: True if the player can pay the price in full.
    """
    storehouse = ctx.player.storehouse
    cost = total_cost(ctx, card, slot_surcharge)

    if any(storehouse.get(good, 0) < quantity
           for good, quantity in cost.items()):
        return False

    left = sum(storehouse.values()) - sum(cost.values())

    return left >= any_good_cost(ctx, card, slot_surcharge)


def affordable_cards(ctx: ActionContext,
                     slot_surcharge: bool = True) -> list[Card]:
    """
    The cards of the display the player can pay for, in display order.

    :param ctx: The card, the player and the game.
    :param slot_surcharge: Whether the slot is paid for on top of the card.
    :return: The cards within reach, empty when none is.
    """
    return [
        card for card in ctx.game_state.market.display
        if can_purchase(ctx, card, slot_surcharge)
    ]


def is_playable(ctx: ActionContext) -> bool:
    """Whether the senator has a card in reach."""
    return bool(affordable_cards(ctx))


# --- Giving the card up ---

def purse_before(ctx: ActionContext) -> dict:
    """Note what the buying is able to change, before it changes any of it."""
    return {
        "storehouse": dict(ctx.player.storehouse),
        "hand": list(ctx.player.hand),
    }


def put_back(ctx: ActionContext, before: dict) -> None:
    """
    Unbuy whatever was bought: the cards out of hand, the goods back in.

    :param ctx: The card, the player and the game.
    :param before: What the player held before the card was played.
    """
    ctx.player.storehouse.clear()
    ctx.player.storehouse.update(before["storehouse"])
    ctx.player.hand[:] = before["hand"]


# --- Buying ---

def buy(ctx: ActionContext, card: Card,
        slot_surcharge: bool = True) -> Flow:
    """
    Buy one card of the display: pay for it and take it into hand.

    :param ctx: The card, the player and the game.
    :param card: The card being bought.
    :param slot_surcharge: Whether the slot is paid for on top of the card.
    :return: True when the card changed hands, False when it is out of reach.
    """
    if not can_purchase(ctx, card, slot_surcharge):
        return False

    yield from pay(ctx, card, slot_surcharge)

    ctx.player.add_to_hand(card)

    return True


def take_out_and_refill(ctx: ActionContext, bought: list[Card]) -> None:
    """
    Take the bought cards out of the display, slide the rest to the left and
    replenish from the stack.

    :param ctx: The card, the player and the game.
    :param bought: The cards that were purchased, in the order they were.
    """
    display = ctx.game_state.market.display

    for card in bought:
        if card in display:
            display.remove(card)

    refill_display(ctx)


def pay(ctx: ActionContext, card: Card,
        slot_surcharge: bool = True) -> Flow:
    """
    Take the price of a card out of the player's storehouse.

    :param ctx: The card, the player and the game.
    :param card: The card being paid for.
    :param slot_surcharge: Whether the slot is paid for on top of the card.
    """
    owed = any_good_cost(ctx, card, slot_surcharge)

    for good, quantity in total_cost(ctx, card, slot_surcharge).items():
        ctx.player.storehouse[good] -= quantity

    for _ in range(owed):
        yield from pay_any_good(ctx)


def pay_any_good(ctx: ActionContext) -> Flow:
    """Take one good of the player's choice out of their storehouse."""
    goods = tuple(ctx.player.goods_in_stock())

    if not goods:
        return

    good = yield ChooseGood(
        "The display slot asks for one good of your choice.", options=goods,
        giving_up=True,
    )
    ctx.player.storehouse[good] -= 1


def refill_display(ctx: ActionContext) -> None:
    """Draw from the stack until the display is full again."""
    market = ctx.game_state.market
    missing = market.display_size - len(market.display)

    if missing > 0:
        market.display.extend(market.draw(missing))
