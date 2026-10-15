"""
File: test_database_controller_live.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests against the real Oracle database, skipped when it is down.
"""
import pytest

from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService

pytestmark = pytest.mark.integration


@pytest.fixture(name="dbc")
def dbc_fixture():
    """A controller on the real database, closed once the test is over."""
    controller = DatabaseController(DatabaseService.from_env())
    yield controller
    controller.close()


def test_italia_provinces(dbc):
    assert len(dbc.select_provinces("Italia")) == 11


def test_starting_houses(dbc):
    assert dbc.select_starting_houses() == 15
