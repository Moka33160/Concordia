"""
File: test_game_controller.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the game loop, without the interface.
"""
import random

import pytest

from concordia.actions.drivers import AiAnswerer
from concordia.controllers.game_controller import GameController
from concordia.managers.card_manager import CardManager
from tests.fake_game import make_game


def make_controller(game, seed=0):
    """A controller over a game already built."""
    controller = GameController.__new__(GameController)
    controller.game = game
    controller.cards = CardManager(game)
    controller.rng = random.Random(seed)
    return controller


def answerer(controller, player):
    """What answers a flow for a seat nobody is clicking for."""
    return AiAnswerer(controller.game, player, controller.rng)


def test_only_playable_cards_are_offered():
    game = make_game()
    controller = make_controller(game)
    player = game.players[0]

    offered = controller.playable_cards(player)

    assert offered
    assert all(card in player.hand for card in offered)
    assert all(
        controller.cards.is_playable(card, player) for card in offered
    )


def test_played_card_goes_to_the_discard_pile():
    game = make_game()
    controller = make_controller(game)
    player = game.next_player
    card = next(c for c in player.hand if c.name == "MERCATOR")
    held = len(player.hand)

    assert controller.cards.play(card, player, answerer(controller, player))
    assert card not in player.hand
    assert len(player.hand) == held - 1
    assert player.discarded_cards == [card]


@pytest.mark.parametrize("seed", range(3))
def test_a_whole_game_ends(seed, capsys):
    game = make_game(seed=seed)
    controller = make_controller(game, seed=seed)
    owned = {
        player.color: len(player.colonists) + len(player.storehouse_colonists)
        for player in game.players
    }

    controller.run()

    # Every seat still holds a legal supply once the dust settles.
    for player in game.players:
        assert player.houses >= 0
        assert all(count >= 0 for count in player.storehouse.values())
        # 12 storage spaces, shared between the goods and the colonists
        # still waiting in reserve.
        assert (
                sum(player.storehouse.values())
                + len(player.storehouse_colonists) <= 12
        )
        # A player never ends up owning more colonists than they were
        # given: the reserve is the cap, not a bottomless supply.
        assert (
                len(player.colonists) + len(player.storehouse_colonists)
                == owned[player.color]
        )
    assert "Traceback" not in capsys.readouterr().out
