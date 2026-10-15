"""
File: way.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: A type of way for lines betweens cities
"""


class Way:
    """A way."""

    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color

    def __repr__(self) -> str:
        return f"Way({self.name!r}, color={self.color!r})"
