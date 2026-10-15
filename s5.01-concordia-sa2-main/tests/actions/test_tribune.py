"""
File: test_tribune.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the TRIBUNE action, on a game built from the real
             database.
"""
import pytest

from concordia.actions import tribune
from concordia.actions.context import ActionContext
from concordia.config import GameConfig
from concordia.controllers.game_builder import GameBuilder
from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService
from concordia.models.card import Card, CardOrigin
from concordia.models.player import AIPlayer
from concordia.state.game_state import GameState
from tests.actions.flows import run

pytestmark = pytest.mark.integration

CARDS = [
    ("TRIBUNE", "MARS", "tribune action"),
    ("ARCHITECT", "JVPITER", "architect action"),
    ("PREFECT", "SATVRNVS", "prefect action"),
    ("MERCATOR", "MERCVRIVS", "mercator action"),
    ("SENATOR", "VESTA", "senator action"),
]


def make_game(nb_players) -> GameState:
    dbc = DatabaseController(DatabaseService.from_env())
    config = GameConfig(argv=["-m",
                              "Italia",
                              "-p",
                              str(nb_players),
                              "-c",
                              "red"], dbc=dbc)
    builder = GameBuilder(config, dbc)
    game: GameState = builder.build()
    make_player(game)
    return game


def make_tribune_ctx(game: GameState, player: AIPlayer) -> ActionContext:
    """The context of that player playing their TRIBUNE."""
    name, god, actions = CARDS[0]
    card = Card(name, god, actions, CardOrigin.STARTING)
    return ActionContext(card, player, game)


def make_player(game: GameState) -> None:
    player = AIPlayer("yellow")
    game.add_player(player)
    game.players[0].discarded_cards.append(CARDS[2])
    game.players[0].discarded_cards.append(CARDS[3])


def test_clear_discarded_cards():
    game = make_game(4)
    player = game.players[0]
    ctx = make_tribune_ctx(game, player)
    print(f"\n{player.discarded_cards}")
    assert len(player.discarded_cards) == 2

    tribune.clear_discard(ctx)
    print(f"\n{player.discarded_cards}")
    assert len(player.discarded_cards) == 0
    assert player.discarded_cards == []

    tribune.clear_discard(ctx)
    assert len(player.discarded_cards) == 0
    assert player.discarded_cards == []


def test_calculate_sestertii():
    game = make_game(4)
    player = game.players[0]
    ctx = make_tribune_ctx(game, player)

    # Depending on the position in the start of the game
    sestertii_start = player.sestertii

    tribune.calculate_sestertii(ctx, [])
    assert player.sestertii == sestertii_start + 0

    player.discarded_cards.append(CARDS[1])
    tribune.calculate_sestertii(ctx, player.discarded_cards)
    assert player.sestertii == sestertii_start + 0

    player.discarded_cards.append(CARDS[1])
    tribune.calculate_sestertii(ctx, player.discarded_cards)
    assert player.sestertii == sestertii_start + 1

    player.sestertii = sestertii_start
    player.discarded_cards.append(CARDS[1])
    player.discarded_cards.append(CARDS[1])
    player.discarded_cards.append(CARDS[1])
    tribune.calculate_sestertii(ctx, player.discarded_cards)
    assert player.sestertii == sestertii_start + 4


def test_purchase_colonist():
    game = make_game(4)
    player = game.players[0]
    ctx = make_tribune_ctx(game, player)
    ways = [colonist.way for colonist in player.storehouse_colonists]

    assert player.storehouse["food"] == 2
    assert player.storehouse["tool"] == 1
    assert sorted(ways) == ["land", "sea"]

    tribune.purchase_colonist(ctx, "land")
    ways = [colonist.way for colonist in player.storehouse_colonists]

    # The colonist costs one food and one tool, and leaves the reserve.
    assert player.storehouse["food"] == 1
    assert player.storehouse["tool"] == 0
    assert ways == ["sea"]


def make_discard_card(name):
    """A card of that name, sitting on a discard pile."""
    return Card(name, None, f"{name} action", CardOrigin.STARTING)


def test_tribune_takes_back_the_discard_pile():
    game = make_game(4)
    player = game.players[0]
    ctx = make_tribune_ctx(game, player)
    player.discarded_cards.append(make_discard_card("ARCHITECT"))
    player.discarded_cards.append(make_discard_card("ARCHITECT"))
    sestertii_start = player.sestertii
    hand_start = len(player.hand)
    discarded = len(player.discarded_cards)

    result, _script = run(tribune.play(ctx), False)

    assert result is True
    assert len(player.hand) == hand_start + discarded
    assert player.discarded_cards == []
    # One sestertius for every card past the third.
    assert player.sestertii == sestertii_start + discarded - 3
