"""
File: test_senator.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the SENATOR action, which buys cards from the display.
"""
from unittest.mock import MagicMock

from concordia.actions import consul, senator
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.market import CardMarket
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from concordia.state.game_state import GameState
from tests.actions.flows import first, run, stop_after

BRICK = Good("brick", 3, "brown", 2, 1)
FOOD = Good("food", 4, "green", 2, 2)
CLOTH = Good("cloth", 7, "blue", 1, 5)

FULL_STOREHOUSE = {"brick": 1, "food": 1, "cloth": 1}


def make_card(name, cost=()):
    """A market card sold for those goods."""
    return Card(name, None, f"{name} action", CardOrigin.MARKET,
                deck_number=1, cost=list(cost))


def make_context(display=(), stack=(), storehouse=None, card="SENATOR"):
    """A player in front of a market display."""
    market = CardMarket()
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

    return ActionContext(make_card(card), player, game_state)


def test_buy_pays_and_adds_to_hand():
    card = make_card("PREFECT", [BRICK, FOOD])
    ctx = make_context(display=[card])

    result, _script = run(senator.buy(ctx, card, slot_surcharge=False))

    assert result is True
    assert ctx.player.hand == [card]
    assert ctx.player.storehouse == {"brick": 0, "food": 0, "cloth": 1}


def test_senator_buys_two_cards_at_most():
    ctx = make_context(display=[make_card(f"CARD{n}") for n in range(4)])

    result, script = run(senator.play(ctx), first, first)

    assert result is True
    assert len(ctx.player.hand) == 2
    assert script.asked == ["ChooseMarketCard", "ChooseMarketCard"]


def test_consul_buys_one_card():
    ctx = make_context(display=[make_card(f"CARD{n}") for n in range(4)],
                       card="CONSUL")

    result, script = run(consul.play(ctx), first)

    assert result is True
    assert len(ctx.player.hand) == 1
    assert script.asked == ["ChooseMarketCard"]


def test_cancel_gives_the_card_back():
    """The bought card is in the hand and still in the display."""
    cheap = make_card("CHEAP", [BRICK])
    other = make_card("OTHER", [FOOD])
    ctx = make_context(display=[cheap, other],
                       storehouse={"brick": 2, "food": 2})

    stop_after(senator.play(ctx), cheap)

    assert [card.name for card in ctx.player.hand] == []
    assert ctx.game_state.market.display == [cheap, other]
    assert ctx.player.storehouse == {"brick": 2, "food": 2}
