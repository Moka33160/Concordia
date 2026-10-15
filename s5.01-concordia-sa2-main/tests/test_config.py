"""
File: test_config.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the command line configuration.
"""
import pytest

from concordia.config import GameConfig
from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService
from tests.db.fakes import FakeConnection, FakeDriver

MAP_LIMIT_ROWS = [("Italia", 2, 4), ("Imperium", 3, 5), ("EU", 2, 5)]
COLOR_ROWS = [("red",), ("green",), ("yellow",), ("blue",), ("black",)]


def make_dbc(settings):
    connection = FakeConnection(rows_by_statement={
        "map_min_n_players": MAP_LIMIT_ROWS,
        "ccd_color_player": COLOR_ROWS,
    })
    driver = FakeDriver(connection)
    return DatabaseController(DatabaseService(settings, driver=driver))


def test_known_map_and_player_count(settings):
    config = GameConfig(
        argv=["-m", "Italia", "-p", "3", "-c", "red"],
        dbc=make_dbc(settings),
    )

    assert config.map == "Italia"
    assert config.nb_players == 3
    assert config.color == "red"


def test_unknown_map_is_rejected(settings):
    with pytest.raises(ValueError, match="Unknown map"):
        GameConfig(argv=["-m", "Atlantis"], dbc=make_dbc(settings))


def test_player_count_defaults_in_range(settings):
    config = GameConfig(argv=["-m", "Italia"], dbc=make_dbc(settings))

    assert 2 <= config.nb_players <= 4


def test_auto_seats_nobody_human(settings):
    config = GameConfig(
        argv=["-m", "Italia", "-p", "3", "--auto"], dbc=make_dbc(settings),
    )

    assert config.auto is True
    assert config.human_position is None


def test_auto_has_a_short_flag(settings):
    config = GameConfig(
        argv=["-m", "Italia", "-a"], dbc=make_dbc(settings),
    )

    assert config.auto is True


def test_auto_leaves_every_color_to_the_ai(settings):
    config = GameConfig(
        argv=["-m", "Italia", "-a"], dbc=make_dbc(settings),
    )

    assert config.color == ""


def test_auto_rejects_a_human_color(settings):
    with pytest.raises(ValueError, match="-c"):
        GameConfig(
            argv=["-m", "Italia", "-c", "red", "--auto"],
            dbc=make_dbc(settings),
        )


def test_a_seat_is_human_without_auto(settings):
    config = GameConfig(argv=["-m", "Italia"], dbc=make_dbc(settings))

    assert config.auto is False
    assert config.human_position is not None
