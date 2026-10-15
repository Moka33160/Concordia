"""
File: test_strategy.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: Tests for the AI strategy, on the small board of fake_game.
"""
from concordia.actions.context import ActionContext
from concordia.actions.requests import ChooseCity
from concordia.actions.strategy import Strategy, evaluate
from tests.fake_game import make_game


def a_game():
    """A game, its first player, and a strategy for that player."""
    game = make_game(nb_players=3, seed=0)
    player = game.players[0]

    return game, player, Strategy(game, player)


def city_named(game, name):
    """A city of the board, by name."""
    return next(
        city for city in game.board.cities()
        if city.display_name == name
    )


def card_named(player, name):
    """A card of a hand, by name."""
    return next(card for card in player.hand if card.name == name)


def test_a_new_province_is_worth_the_most():
    game, _player, plan = a_game()

    # Massilia makes cloth, which MINERVA pays more for than brick.
    assert plan.build_worth(city_named(game, "Massilia")) > \
        plan.build_worth(city_named(game, "Ostia"))


def test_ai_always_builds_when_offered():
    """The build request is optional, but the AI should never refuse it."""
    game, player, plan = a_game()
    sites = (city_named(game, "Massilia"), city_named(game, "Ostia"))
    request = ChooseCity("Build?", options=sites, optional=True)

    assert plan(request) is city_named(game, "Massilia")


def test_tribune_is_worth_more_with_an_empty_hand():
    game, player, _plan = a_game()
    tribune = card_named(player, "TRIBUNE")
    player.discarded_cards.extend(
        card for card in player.hand if card is not tribune
    )
    player.hand[:] = [tribune]

    worth = evaluate(tribune, ActionContext(tribune, player, game))

    assert worth > 5.0
