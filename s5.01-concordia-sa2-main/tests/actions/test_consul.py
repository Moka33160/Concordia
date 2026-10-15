"""
File: test_consul.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the CONSUL action, which buys one card of the market
             display and pays it with the goods printed on it alone: the
             goods drawn above the display slot are the surcharge of the
             SENATOR, not of the CONSUL.
"""
import random
from unittest.mock import MagicMock

from concordia import actions
from concordia.actions import consul, senator
from concordia.actions.context import ActionContext
from concordia.actions.drivers import AiAnswerer
from concordia.models.card import Card, CardOrigin
from concordia.models.market import CardMarket, DisplaySlot
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from concordia.state.game_state import GameState
from tests.actions.flows import first, run

BRICK = Good("brick", 3, "brown", 2, 1)
FOOD = Good("food", 4, "green", 2, 2)
CLOTH = Good("cloth", 7, "blue", 1, 5)

FULL_STOREHOUSE = {"brick": 1, "food": 1, "cloth": 1}

ANY_GOOD_SLOT = DisplaySlot(1, True)
CLOTH_SLOT = DisplaySlot(1, False, "cloth", 1)

# The card question is optional: None buys nothing.
NOTHING = None


def make_card(name, cost=()):
    """A card of the market, sold for the given goods."""
    return Card(name, None, f"{name} action", CardOrigin.MARKET,
                deck_number=1, cost=list(cost))


def make_context(display=(), stack=(), storehouse=None, slots=()):
    """A player standing in front of a market display, CONSUL in hand."""
    market = CardMarket(list(slots))
    market.display = list(display)
    market.stack = list(stack)

    game_state = MagicMock(spec=GameState)
    game_state.market = market
    game_state.goods_by_name = {
        good.name: good for good in (BRICK, FOOD, CLOTH)
    }

    player = AIPlayer("red")
    player.fill_storehouse(
        [], dict(FULL_STOREHOUSE if storehouse is None else storehouse)
    )

    return ActionContext(make_card("CONSUL"), player, game_state)


# ---- One card, and one only ---- #

def test_play_buys_a_single_card():
    wanted = make_card("FIRST", [BRICK])
    other = make_card("SECOND", [FOOD])
    ctx = make_context(display=[wanted, other])

    result, script = run(consul.play(ctx), first)

    assert result is True
    assert script.asked == ["ChooseMarketCard"]
    assert ctx.player.hand == [wanted]
    assert ctx.game_state.market.display == [other]
    assert ctx.player.storehouse == {"brick": 0, "food": 1, "cloth": 1}


def test_play_pays_the_price_printed_on_the_card():
    card = make_card("ARCHITECT", [BRICK, BRICK, FOOD])
    ctx = make_context(display=[card], storehouse={"brick": 3, "food": 2})

    result, _script = run(consul.play(ctx), first)

    assert result is True
    assert ctx.player.hand == [card]
    assert ctx.player.storehouse == {"brick": 1, "food": 1}


def test_play_takes_the_card_out_of_the_display_and_refills_behind_it():
    display = [make_card(f"CARD-{index}", [BRICK]) for index in range(7)]
    drawn = make_card("DRAWN")
    ctx = make_context(display=display, stack=[drawn],
                       storehouse={"brick": 1})

    run(consul.play(ctx), first)

    market = ctx.game_state.market
    assert len(market.display) == 7
    assert market.display[-1] is drawn
    assert market.stack == []


# ---- The display slot is not the CONSUL's business ---- #

def test_play_ignores_the_good_named_by_the_display_slot():
    card = make_card("A", [BRICK])
    ctx = make_context(display=[card], storehouse={"brick": 1, "cloth": 1},
                       slots=[CLOTH_SLOT])

    result, _script = run(consul.play(ctx), first)

    assert result is True
    assert ctx.player.hand == [card]
    assert ctx.player.storehouse == {"brick": 0, "cloth": 1}


def test_play_ignores_a_slot_asking_for_a_good_at_will():
    card = make_card("A", [BRICK])
    ctx = make_context(display=[card], storehouse={"brick": 1, "cloth": 1},
                       slots=[ANY_GOOD_SLOT])

    result, _script = run(consul.play(ctx), first)

    assert result is True
    assert ctx.player.storehouse == {"brick": 0, "cloth": 1}


def test_play_never_asks_the_person_for_a_good_to_pay_the_slot():
    card = make_card("A", [BRICK])
    ctx = make_context(display=[card], storehouse={"brick": 1, "cloth": 1},
                       slots=[ANY_GOOD_SLOT])

    # One question only, the card: no ChooseGood for the slot.
    result, script = run(consul.play(ctx), first)

    assert result is True
    assert script.asked == ["ChooseMarketCard"]


def test_play_buys_what_the_senator_could_not_have_paid():
    card = make_card("A", [BRICK])
    surcharged = make_context(display=[card], storehouse={"brick": 1},
                              slots=[ANY_GOOD_SLOT])

    assert senator.affordable_cards(surcharged) == []

    ctx = make_context(display=[make_card("A", [BRICK])],
                       storehouse={"brick": 1}, slots=[ANY_GOOD_SLOT])

    result, _script = run(consul.play(ctx), first)

    assert result is True
    assert ctx.player.storehouse == {"brick": 0}


# ---- Buying nothing ---- #

def test_play_stops_when_the_player_buys_nothing():
    card = make_card("FIRST", [BRICK])
    ctx = make_context(display=[card])

    result, _script = run(consul.play(ctx), NOTHING)

    assert result is True
    assert ctx.player.hand == []
    assert ctx.game_state.market.display == [card]


def test_play_refuses_when_no_card_of_the_display_can_be_paid():
    ctx = make_context(display=[make_card("DEAR", [CLOTH])],
                       storehouse={"brick": 1})

    result, script = run(consul.play(ctx))

    assert result is False
    assert script.asked == []
    assert ctx.player.hand == []


def test_play_refuses_when_the_display_is_empty():
    ctx = make_context()

    result, script = run(consul.play(ctx))

    assert result is False
    assert script.asked == []


# ---- The AI ---- #

def test_play_lets_an_ai_buy_the_dearest_card_it_can_pay():
    cheap = make_card("CHEAP", [BRICK])
    dear = make_card("DEAR", [CLOTH])
    middle = make_card("MIDDLE", [FOOD])
    ctx = make_context(display=[cheap, dear, middle])
    ai = AiAnswerer(ctx.game_state, ctx.player, random.Random(0))

    result, _script = run(consul.play(ctx), ai)

    assert result is True
    assert ctx.player.hand == [dear]
    assert ctx.game_state.market.display == [cheap, middle]


# ---- Registration ---- #

def test_the_consul_action_is_registered_under_its_card_name():
    assert actions.ACTIONS["CONSUL"] is consul.play
