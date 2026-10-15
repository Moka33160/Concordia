"""
File: test_game_builder.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the game setup, run against a fake database.
"""
import random

from concordia.config import GameConfig
from concordia.controllers.game_builder import GameBuilder
from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService
from concordia.models.card import CardOrigin
from concordia.models.player import AIPlayer, HumanPlayer
from tests.db.fakes import FakeConnection, FakeDriver

CAPITAL_ROW = (" R O M A ", None, 338, 207)
PROVINCE_ROWS = [("VENETIA", "I", 130, 67), ("LIGVRIA", "II", 79, 303)]
CITIES_BY_PROVINCE = {
    "VENETIA": [("VERONA", "A", 129, 93)],
    "LIGVRIA": [("GENVA", "B", 105, 248)],
}
ROUTE_ROWS = [(" R O M A ", "VERONA", "land"), ("VERONA", "GENVA", "sea")]
WAY_ROWS = [("land", "brown"), ("sea", "blue"), ("air", "cyan")]
MAP_BOUNDS_ROW = (692, 373)
CITY_TOKEN_ROWS = [("A", "brick", 1), ("B", "cloth", 1)]
GOOD_ROWS = [
    ("brick", 3, "brown", 2, 1),
    ("cloth", 7, "blue", 1, 5),
]
GOOD_BUILD_COST_ROWS = [
    ("brick", "food"),
    ("cloth", "brick"),
    ("cloth", "cloth"),
]
DESCRIPTION_ROW = (
    "Concordia", 2013, "Mac Gerdts", "PD-Verlag", "2-5", "12", 100
)
ARTIST_ROWS = [("Marina Fahrenbach",), ("Dominik Mayer",)]
DISPLAY_AREA_ROWS = [
    (1, "N", None, None),
    (2, "Y", None, None),
    (3, "Y", "cloth", 1),
]
GOD_ROWS = [
    ("JVPITER", "the sky", "1 VP per house in a non-brick city", "...", 1),
    ("SATVRNVS", "the harvest", "1 VP per populated province", "...", 1),
    ("MERCVRIVS", "the trade", "2 VP per kind of good produced", "...", 2),
    ("MARS", "the war", "2 VP per colonist", "...", 2),
    ("VESTA", "the hearth", "1 VP per 10 sestertii", "...", 1),
    # MINERVA scores per specialist, which the column cannot hold: see
    # concordia.rules.
    ("MINERVA", "the craft", "VP per city of the specialist", "...", None),
]
CARD_DEFINITION_ROWS = [
    ("CONCORDIA", "CONCORDIA", "concordia action", "concordia example"),
    ("PRÆFECTVS MAGNVS", None, "praefectus action", None),
    ("TRIBUNE", "MARS", "tribune action", "tribune example"),
    ("ARCHITECT", "JVPITER", "architect action", "architect example"),
    ("PREFECT", "SATVRNVS", "prefect action", None),
    ("MERCATOR", "MERCVRIVS", "mercator action", None),
    ("SENATOR", "VESTA", "senator action", None),
    ("WEAVER", "MINERVA", "weaver action", None),
]
PERSONALITY_CARD_ROWS = [
    ("ARCHITECT", "JVPITER", 1, "architect action", None,
     "architect example"),
    ("PREFECT", "SATVRNVS", 1, "prefect action", None, None),
    ("MERCATOR", "MERCVRIVS", 2, "mercator action", "cloth", None),
    ("WEAVER", "MINERVA", 2, "weaver action", None, None),
]
CARD_COST_ROWS = [
    ("ARCHITECT", "brick"),
    ("ARCHITECT", "cloth"),
    ("MERCATOR", "cloth"),
]
STARTING_COLONIST_ROWS = [("land", 3, 1), ("sea", 3, 1), ("air", 0, 0)]
STARTING_GOOD_ROWS = [("brick", 1), ("cloth", 1)]
STARTING_CARD_ROWS = [("TRIBUNE", 1), ("SENATOR", 1), ("MERCATOR", 1)]
STARTING_SESTERTIUS_ROWS = [(1, 5, 25), (2, 6, 26)]
MAP_LIMIT_ROWS = [("Italia", 2, 4)]
COLOR_ROWS = [("red",), ("green",)]


def make_dbc(settings):
    """
    A fake DatabaseController answering the whole setup with a 2-province
    mini map.
    """
    connection = FakeConnection(rows_by_statement={
        # `good_build_cost` first: its statement also mentions `ccd_good) g`.
        "good_build_cost": GOOD_BUILD_COST_ROWS,
        "ccd_description.artists": ARTIST_ROWS,
        "ccd_description.edition_year": [DESCRIPTION_ROW],
        "ccd_display_area": DISPLAY_AREA_ROWS,
        "map_capital.city_name": [CAPITAL_ROW],
        "n.numeral_roman = p.province_roman_num": PROVINCE_ROWS,
        "province_city) ci": (
            lambda params: CITIES_BY_PROVINCE[params["province_name"]]
        ),
        "map_line) l": ROUTE_ROWS,
        "ccd_way) w": WAY_ROWS,
        "map_max_coordinates": [MAP_BOUNDS_ROW],
        "ccd_city_token) t": CITY_TOKEN_ROWS,
        "ccd_good) g": GOOD_ROWS,
        "ccd_god) g": GOD_ROWS,
        "card_for_sale_deck_diplomat": PERSONALITY_CARD_ROWS,
        "card_for_sale_cost": CARD_COST_ROWS,
        "SELECT cd.card_name, cd.card_god, cd.card_action, ":
            CARD_DEFINITION_ROWS,
        "setup_p_n_houses": [(15,)],
        "setup_p_colon_way": STARTING_COLONIST_ROWS,
        "setup_p_good_good": STARTING_GOOD_ROWS,
        "setup_p_card_card": STARTING_CARD_ROWS,
        "setup_p_se_order_of_play": STARTING_SESTERTIUS_ROWS,
        "map_min_n_players": MAP_LIMIT_ROWS,
        "ccd_color_player": COLOR_ROWS,
    })
    driver = FakeDriver(connection)
    return DatabaseController(DatabaseService(settings, driver=driver))


def make_game(settings, nb_players=2):
    dbc = make_dbc(settings)
    config = GameConfig(
        argv=["-m", "Italia", "-p", str(nb_players), "-c", "red"], dbc=dbc
    )
    builder = GameBuilder(config, dbc, rng=random.Random(42))
    return builder.build()


def test_build_returns_a_full_game_state(settings):
    game = make_game(settings)

    assert game.board is not None
    assert game.market is not None
    assert len(game.players) == 2


def test_build_deals_the_starting_hand(settings):
    """A starting card keeps the god of its ccd_card row."""
    game = make_game(settings)

    gods_by_card = {
        name: god_name for name, god_name, _action, _example
        in CARD_DEFINITION_ROWS
    }
    for player in game.players:
        for card in player.hand:
            assert card.origin is CardOrigin.STARTING
            assert card.god is not None
            assert card.god.name == gods_by_card[card.name]


def test_build_is_deterministic(settings):
    dbc = make_dbc(settings)
    config = GameConfig(argv=["-m", "Italia", "-p", "2", "-c", "red"], dbc=dbc)

    first = GameBuilder(config, dbc, rng=random.Random(42)).build()
    second = GameBuilder(config, dbc, rng=random.Random(42)).build()

    assert [player.color for player in first.players] == [
        player.color for player in second.players
    ]
    assert first.next_player.color == second.next_player.color


def test_auto_seats_only_ai_players(settings):
    dbc = make_dbc(settings)
    config = GameConfig(argv=["-m", "Italia", "-p", "2", "-a"], dbc=dbc)

    game = GameBuilder(config, dbc, rng=random.Random(42)).build()

    assert len(game.players) == 2
    assert all(isinstance(player, AIPlayer) for player in game.players)


def test_one_seat_is_human_without_auto(settings):
    game = make_game(settings)

    assert sum(
        isinstance(player, HumanPlayer) for player in game.players
    ) == 1
