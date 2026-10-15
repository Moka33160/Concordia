"""
File: fake_game.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: A small game built by hand, for the tests that need no database.
"""
import random
from types import SimpleNamespace

from concordia.models.board import Board
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.market import CardMarket, DisplaySlot
from concordia.models.player import AIPlayer
from concordia.models.province import Province
from concordia.models.resource import Good
from concordia.models.token import BonusMarker, CityToken
from concordia.state.game_state import GameState

BRICK = Good("brick", 3, "#8b5a2b", 2, 1, ["brick", "food"])
FOOD = Good("food", 4, "#c8a13a", 2, 1, ["brick", "food"])
CLOTH = Good("cloth", 7, "#3b5f9e", 4, 5, ["brick", "cloth"])
GOODS = (BRICK, FOOD, CLOTH)

# Every card that has an action, so a hand can play all of them.
HAND_CARDS = (
    "ARCHITECT", "COLONIST", "CONSUL", "DIPLOMAT", "MERCATOR", "PREFECT",
    "SENATOR", "TRIBUNE", "MASON", "FARMER", "WEAVER",
)


def make_card(name, deck=None, cost=(), good=None):
    """A card with that name and that price."""
    origin = CardOrigin.MARKET if deck else CardOrigin.STARTING
    return Card(name, None, f"{name} action", origin, deck_number=deck,
                cost=list(cost), good=good)


def make_board():
    """A board with the capital, two provinces and four cities."""
    board = Board("Test")
    board.set_bounds(100, 100)
    board.add_way("land", "#8b6f47")
    board.add_way("sea", "#3b5f9e")

    capital = City(" R O M A ", "A", 3, x=50, y=50)
    board.set_capital(capital)

    layout = [
        ("Italia", "I", [("Ostia", BRICK, 40, 40), ("Pisae", FOOD, 60, 40)]),
        ("Gallia", "II", [("Massilia", CLOTH, 40, 60),
                          ("Narbo", BRICK, 60, 60)]),
    ]

    for name, numeral, cities in layout:
        province = Province(name, numeral, x=50, y=50)
        for city_name, good, x, y in cities:
            city = City(city_name, "A", 3, x=x, y=y)
            city.set_token(CityToken("A", good))
            city.reveal()
            province.add_city(city)
            board.index_city(city)
        province.set_bonus_marker(BonusMarker(province.most_valuable_good()))
        board.add_province(province)

    cities = [city for city in board.cities() if city is not capital]
    for city in cities:
        board.add_route(capital.name, city.name, "land")
    board.add_route(cities[0].name, cities[-1].name, "sea")

    return board


def make_market(rng):
    """A market with seven display slots."""
    market = CardMarket([
        DisplaySlot(1, any_good_required=False),
        DisplaySlot(2, any_good_required=True),
        *[DisplaySlot(n, any_good_required=False, good="brick", n_goods=1)
          for n in range(3, 8)],
    ])

    for deck in (1, 2):
        for name in HAND_CARDS:
            market.add_card(make_card(name, deck=deck, cost=[BRICK],
                                      good=CLOTH))

    market.set_aside(make_card("CONCORDIA"))
    market.prepare_stack(nb_players=4, rng=rng)
    return market


def make_game(nb_players=3, seed=0, hand=HAND_CARDS):
    """A game ready to be played."""
    rng = random.Random(seed)
    # The scoring only needs the map name and the number of players.
    game = GameState(
        config=SimpleNamespace(map="Test", nb_players=nb_players)
    )
    board = make_board()

    game.set_board(board)
    game.set_market(make_market(rng))
    game.set_goods({good.name: good for good in GOODS})

    for color in ("red", "blue", "green", "yellow")[:nb_players]:
        player = AIPlayer(color, rng)
        player.init_supply(5)
        player.fill_storehouse(
            [Colonist("land"), Colonist("sea")],
            {"brick": 2, "food": 2, "cloth": 1},
        )
        player.place_colonist("land", board.capital)
        player.sestertii = 10
        for name in hand:
            player.add_to_hand(
                make_card(name, good=CLOTH if name in
                          ("MASON", "FARMER", "WEAVER") else None)
            )
        game.add_player(player)

    game.set_start_player(rng)
    return game
