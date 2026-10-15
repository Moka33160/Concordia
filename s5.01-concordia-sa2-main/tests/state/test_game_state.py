"""
File: test_game_state.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the state of a game: turns, rounds and seating order.
"""


from concordia.models.card import Card, CardOrigin
from tests.fake_game import make_game


def test_game_starts_on_turn_one():
    game = make_game(nb_players=3)

    assert game.turn == 1
    assert game.round == 1


def test_next_player_follows_the_seating_order():
    game = make_game(nb_players=3)
    seats = game.players
    start = seats.index(game.next_player)

    game.advance_to_next_player()

    assert game.next_player is seats[(start + 1) % len(seats)]


def marker_card():
    """The PRAEFECTVS MAGNVS card."""
    return Card("PRÆFECTVS MAGNVS", None, "...", CardOrigin.AWARD)


def test_praefectus_magnus_goes_to_the_next_seat():
    """
    The marker goes to the player on the right, so the seat before this
    one in the order of play.
    """
    game = make_game(nb_players=3)
    seats = game.players
    seats[1].give_praefectus_magnus(marker_card())

    game.pass_praefectus_magnus(seats[1])

    assert seats[0].has_praefectus_magnus is True
    assert seats[1].has_praefectus_magnus is False
