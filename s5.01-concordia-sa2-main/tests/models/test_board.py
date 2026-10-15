"""
File: test_board.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the board: routes, city tokens and bonus markers.
"""
import random

from concordia.models.board import Board
from concordia.models.city import City
from concordia.models.province import Province
from concordia.models.resource import Good
from concordia.models.token import CityToken

BRICK = Good(
    "brick", value=3, color="brown", bonus_sestertii=2,
    build_cost_sestertii=1,
)
CLOTH = Good(
    "cloth", value=7, color="blue", bonus_sestertii=1,
    build_cost_sestertii=5,
)


def make_board():
    board = Board("Italia")
    roma = City(" R O M A ", None, 0, 338, 207)
    board.set_capital(roma)

    verona = City("VERONA", "A", 3, 129, 93)
    cosa = City("COSA", "B", 3, 273, 225)
    board.index_city(verona)
    board.index_city(cosa)

    return board, roma, verona, cosa


def test_distribute_city_tokens():
    board, roma, verona, cosa = make_board()
    tokens = [CityToken("A", BRICK), CityToken("B", CLOTH)]

    board.distribute_city_tokens(tokens, random.Random(1))

    assert verona.token is not None and verona.token.revealed
    assert cosa.token is not None and cosa.token.revealed
    assert roma.token is None


def test_assign_bonus_markers():
    board, _, verona, cosa = make_board()
    province = Province("VENETIA", "I")
    province.add_city(verona)
    province.add_city(cosa)
    board.add_province(province)
    board.distribute_city_tokens(
        [CityToken("A", BRICK), CityToken("B", CLOTH)], random.Random(1)
    )

    board.assign_bonus_markers()

    assert province.bonus_marker.good is CLOTH


def test_routes_at_a_city():
    board, roma, verona, cosa = make_board()
    board.add_route(roma.name, verona.name, "land")
    board.add_route(roma.name, cosa.name, "sea")
    board.add_route(verona.name, cosa.name, "land")

    found = board.routes_at(roma)

    assert {route.other_end(roma) for route in found} == {verona, cosa}


def test_routes_next_to_a_route():
    board, roma, verona, cosa = make_board()
    board.add_route(roma.name, verona.name, "land")
    board.add_route(verona.name, cosa.name, "land")
    board.add_route(roma.name, cosa.name, "land")
    first, second, third = board.routes

    assert set(board.routes_next_to(first)) == {second, third}
