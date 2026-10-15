"""
File: test_settings.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 03-09-2026
Description: Tests for the Oracle connection settings.
"""


from concordia.settings import OracleSettings

VALID_ENV = {
    "ORACLE_HOSTNAME": "localhost",
    "ORACLE_PORT": "1521",
    "ORACLE_SERVICE_NAME": "IUT12c",
    "ORACLE_USERNAME": "ETD",
    "ORACLE_PASSWORD": "secret",
}


def test_from_env_reads_the_variables():
    settings = OracleSettings.from_env(VALID_ENV)

    assert settings.hostname == "localhost"
    assert settings.port == 1521
    assert settings.service_name == "IUT12c"
    assert settings.username == "ETD"
    assert settings.password == "secret"


def test_dsn_format():
    settings = OracleSettings.from_env(VALID_ENV)

    assert settings.dsn == "localhost:1521/IUT12c"


def test_repr_hides_the_password():
    settings = OracleSettings.from_env(
        dict(VALID_ENV, ORACLE_PASSWORD="hunter2")
    )

    assert "hunter2" not in repr(settings)
