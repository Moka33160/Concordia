"""
File: test_database_service.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 03-09-2026
Description: Tests for the database service, with a fake driver.
"""
import pytest

from concordia.db.database_service import DatabaseError, DatabaseService
from tests.db.fakes import FakeConnection, FakeDriver


def make_service(settings, connection):
    driver = FakeDriver(connection)
    return DatabaseService(settings, driver=driver), driver


def test_connect_uses_the_settings(settings):
    service, driver = make_service(settings, FakeConnection())

    service.connect()

    assert driver.credentials == {
        "user": "ETD",
        "password": "secret",
        "dsn": "localhost:1521/IUT12c",
    }


def test_fetch_all_binds_and_returns_the_rows(settings):
    connection = FakeConnection(rows=[(1, "Roma"), (2, "Neapolis")])
    service, _ = make_service(settings, connection)
    service.connect()

    rows = service.fetch_all(
        "SELECT id, name FROM city WHERE id > :min_id", {"min_id": 0}
    )

    assert rows == [(1, "Roma"), (2, "Neapolis")]
    assert connection.statements == [
        ("SELECT id, name FROM city WHERE id > :min_id", {"min_id": 0})
    ]


def test_query_without_connection_raises(settings):
    service, _ = make_service(settings, FakeConnection())

    with pytest.raises(DatabaseError, match="not connected"):
        service.fetch_all("SELECT 1 FROM dual")
