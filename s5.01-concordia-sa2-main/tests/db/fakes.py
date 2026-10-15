"""
File: fakes.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Fake oracledb objects used by the database tests.
"""


class FakeCursor:
    """Cursor that records the statements and replays canned rows."""

    def __init__(self, connection):
        self._connection = connection
        self._rows = []
        self.rowcount = connection.rowcount
        self.closed = False

    def execute(self, statement, parameters):
        """
        Record the statement, then look up the rows it should answer
        with.
        """
        self._connection.statements.append((statement, parameters))
        self._rows = self._connection.rows_for(statement, parameters)

    def fetchall(self):
        """Return every canned row."""
        return list(self._rows)

    def fetchone(self):
        """Return the first canned row, or None when there is none."""
        return self._rows[0] if self._rows else None

    def close(self):
        """Mark the cursor as closed."""
        self.closed = True


class FakeConnection:
    """Connection handing out fake cursors and counting commits."""

    def __init__(self, rows=(), rowcount=None, rows_by_statement=None):
        self.rows = list(rows)
        self.rowcount = len(self.rows) if rowcount is None else rowcount
        self.rows_by_statement = dict(rows_by_statement or {})
        self.statements = []
        self.commits = 0
        self.closed = False
        self.cursors = []

    def cursor(self):
        """Open a fake cursor bound to this connection."""
        cursor = FakeCursor(self)
        self.cursors.append(cursor)
        return cursor

    def rows_for(self, statement, parameters):
        """Look up the rows a statement should answer with."""
        for fragment, rows in self.rows_by_statement.items():
            if fragment in statement:
                return list(rows(parameters) if callable(rows) else rows)
        return list(self.rows)

    def commit(self):
        """Count the commit."""
        self.commits += 1

    def close(self):
        """Mark the connection as closed."""
        self.closed = True


class FakeDriver:
    """Stand-in for the `oracledb` module."""

    def __init__(self, connection):
        self.connection = connection
        self.credentials = None
        self.connect_calls = 0

    def connect(self, user, password, dsn):
        """Record the credentials and hand back the fake connection."""
        self.connect_calls += 1
        self.credentials = {"user": user, "password": password, "dsn": dsn}
        return self.connection
