"""
File: database_service.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 03-09-2026
Description: Thin service owning the Oracle connection and running SQL
             statements.
"""
from collections.abc import Mapping, Sequence
from typing import Any

import oracledb

from concordia.settings import OracleSettings, load_oracle_settings

Parameters = Mapping[str, Any] | Sequence[Any] | None
Row = tuple[Any, ...]


class DatabaseError(RuntimeError):
    """Raised when the service is used outside of an open connection."""


class DatabaseService:
    """Open an Oracle connection and run statements on it."""

    def __init__(self, settings: OracleSettings, driver=oracledb) -> None:
        self._settings = settings
        self._driver = driver
        self._connection = None

    @classmethod
    def from_env(cls, driver=oracledb) -> "DatabaseService":
        """Build a service from the credentials stored in the .env file."""
        return cls(load_oracle_settings(), driver=driver)

    @property
    def is_connected(self) -> bool:
        """Whether a connection is currently open."""
        return self._connection is not None

    def connect(self) -> "DatabaseService":
        """Open the connection, or keep the one already open."""
        if self._connection is None:
            self._connection = self._driver.connect(
                user=self._settings.username,
                password=self._settings.password,
                dsn=self._settings.dsn,
            )
        return self

    def close(self) -> None:
        """Close the connection if there is one."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def fetch_all(
            self, statement: str, parameters: Parameters = None
    ) -> list[Row]:
        """Run a query and return every row."""
        with self._cursor(statement, parameters) as cursor:
            return cursor.fetchall()

    def fetch_one(
            self, statement: str, parameters: Parameters = None
    ) -> Row | None:
        """Run a query and return its first row, or None when there is none."""
        with self._cursor(statement, parameters) as cursor:
            return cursor.fetchone()

    def execute(self, statement: str, parameters: Parameters = None) -> int:
        """
        Run an INSERT/UPDATE/DELETE, commit it and return the affected row
        count.
        """
        with self._cursor(statement, parameters) as cursor:
            affected_rows = cursor.rowcount
        self._connection.commit()
        return affected_rows

    def _cursor(self, statement: str, parameters: Parameters):
        if self._connection is None:
            raise DatabaseError(
                "Database service is not connected, call connect() first"
            )
        cursor = self._connection.cursor()
        cursor.execute(statement, parameters if parameters is not None else {})
        return _ClosingCursor(cursor)

    def __enter__(self) -> "DatabaseService":
        return self.connect()

    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()


class _ClosingCursor:
    """
    Context manager closing the wrapped cursor, whatever the driver provides.
    """

    def __init__(self, cursor) -> None:
        self._cursor = cursor

    def __enter__(self):
        return self._cursor

    def __exit__(self, exception_type, exception, traceback) -> None:
        self._cursor.close()
