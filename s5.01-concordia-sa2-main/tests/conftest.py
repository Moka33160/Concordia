"""
File: conftest.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Fixtures shared by the test suite.
"""
import socket

import pytest

from concordia.settings import OracleSettings

ORACLE_HOST = "localhost"
ORACLE_PORT = 1521


def _oracle_is_reachable() -> bool:
    """
    Whether something is listening on the Oracle port, without opening a
    session.
    """
    try:
        conn = socket.create_connection(
            (ORACLE_HOST, ORACLE_PORT), timeout=0.5
        )
        with conn:
            return True
    except OSError:
        return False


@pytest.fixture(name="settings")
def settings_fixture():
    """Settings for a database nobody connects to."""
    return OracleSettings(
        hostname="localhost",
        port=1521,
        service_name="IUT12c",
        username="ETD",
        password="secret",
    )


def pytest_collection_modifyitems(items):
    """
    Skip every integration test when no database answers on the Oracle
    port.
    """
    if _oracle_is_reachable():
        return
    skip_offline = pytest.mark.skip(
        reason="Oracle database is not reachable on localhost:1521"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_offline)
