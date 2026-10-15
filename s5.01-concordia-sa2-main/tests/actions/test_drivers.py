"""
File: test_drivers.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the flow runner and for the AI answerer.
"""
import random


from concordia.actions.drivers import AiAnswerer, run_flow
from concordia.actions.requests import ChooseCity, ChooseGood
from concordia.models.player import AIPlayer
from concordia.models.resource import Good
from concordia.state.game_state import GameState

BRICK = Good("brick", 3, "#8b5a2b", 2, 1)
CLOTH = Good("cloth", 7, "#3b5f9e", 1, 5)


def make_game(goods=(BRICK, CLOTH)) -> GameState:
    """A game with only its goods, which is all the driver reads."""
    game = GameState(config=None)
    game.set_goods({good.name: good for good in goods})
    return game


def make_answerer(player=None, seed=0) -> AiAnswerer:
    """An AI answerer with a seeded generator."""
    return AiAnswerer(
        make_game(), player or AIPlayer("red"), random.Random(seed)
    )


def test_run_flow_returns_the_result():
    def flow():
        yield ChooseCity("Where to?", options=("Roma",))
        return True

    assert run_flow(flow(), lambda request: "Roma") is True


def test_run_flow_sends_the_answers():
    seen = []

    def flow():
        first = yield ChooseCity("First?", options=("Roma", "Ostia"))
        second = yield ChooseCity("Second?", options=("Ostia",))
        seen.extend([first, second])
        return True

    run_flow(flow(), lambda request: request.options[-1])

    assert seen == ["Ostia", "Ostia"]


# Only the contract is checked here: the answerer always gives back
# something the request accepts. Whether the answer is a good one is
# tested in test_strategy.py.

def test_ai_picks_an_offered_option():
    request = ChooseGood("Which good?", options=("brick", "cloth"))
    answerer = make_answerer()

    for _ in range(20):
        assert answerer(request) in request.options
