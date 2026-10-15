"""
File: test_database_controller.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Tests for the queries of the database controller.
"""
from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService
from tests.db.fakes import FakeConnection, FakeDriver

CCD_ROWS = [(1, "Architectus"), (2, "Diplomat"), (3, "Mercator")]


def make_controller(settings, rows=()):
    connection = FakeConnection(rows=rows)
    driver = FakeDriver(connection)
    service = DatabaseService(settings, driver=driver)
    return DatabaseController(service), connection, driver


def test_get_concordia_ccd(settings):
    controller, connection, _ = make_controller(settings, rows=CCD_ROWS)

    rows = controller.get_concordia_ccd()

    assert rows == CCD_ROWS
    assert connection.statements == [("SELECT * FROM T_CONCORDIA_CCD", {})]


def test_reads_reuse_the_connection(settings):
    controller, _, driver = make_controller(settings, rows=CCD_ROWS)

    controller.get_concordia_ccd()
    controller.get_concordia_ccd()

    assert driver.connect_calls == 1


def test_select_good_build_costs(settings):
    rows = [("brick", "food"), ("cloth", "brick"), ("cloth", "cloth")]
    controller, connection, _ = make_controller(settings, rows=rows)

    assert controller.select_good_build_costs() == rows
    statement, _ = connection.statements[0]
    assert "TABLE(g.good_build_cost) b" in statement
