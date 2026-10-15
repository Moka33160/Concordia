"""
File: test_mercator.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the MERCATOR action: the sestertii and the two trades.
"""
from unittest.mock import MagicMock

from concordia.actions import mercator
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from tests.actions.flows import option, run

FOOD = Good("food", 3, "#c8a13a", 2, 1)
TOOL = Good("tool", 5, "#8a8a8a", 3, 2)

BUY = option("buy")
SELL = option("sell")

# A mercator allows two trades, so a test doing only one has to decline
# the second with PASS.
PASS = None


def create_player(sestertii=10, food=5, tool=5):
    """A player with a given purse and storehouse."""
    player = AIPlayer("red")
    player.sestertii = sestertii
    player.fill_storehouse([], {"food": food, "tool": tool})
    return player


def create_ctx(player, origin=CardOrigin.MARKET, goods=(FOOD, TOOL)):
    """That player playing a MERCATOR of the given origin."""
    game_state = MagicMock()
    game_state.goods_by_name = {good.name: good for good in goods}

    card = Card("MERCATOR", None, "mercator action", origin, deck_number=2)
    return ActionContext(card, player, game_state)


def test_market_mercator_gives_five_sestertii():
    player = create_player(sestertii=0, food=0, tool=0)

    run(mercator.play(create_ctx(player)), PASS, PASS)

    assert player.sestertii == 5


def test_sell_fills_the_purse():
    player = create_player(sestertii=0, food=2, tool=0)

    result, script = run(
        mercator.play(create_ctx(player)), SELL, "food", 2, PASS,
    )

    assert result is True
    assert script.asked[:3] == ["ChooseOption", "ChooseGood", "ChooseAmount"]
    assert player.storehouse["food"] == 0
    # 5 for the card, then 2 food at 3 each.
    assert player.sestertii == 11


def test_buy_fills_the_storehouse():
    player = create_player(sestertii=10, food=0, tool=0)

    run(mercator.play(create_ctx(player)), BUY, "food", 2, PASS)

    assert player.storehouse["food"] == 2
    # 10 in purse plus 5 for the card, less 2 food at 3 each.
    assert player.sestertii == 9


def test_mercator_offers_two_trades():
    player = create_player(sestertii=0, food=4, tool=4)

    _result, script = run(
        mercator.play(create_ctx(player)),
        SELL, "food", 1, SELL, "tool", 1,
    )

    assert script.asked.count("ChooseOption") == 2
