"""
File: token.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The city tokens dealt on the board and the bonus markers of the
             provinces.
"""
from concordia.models.resource import Good


class CityToken:
    """A city token, face down until it is revealed during the setup."""

    def __init__(self, roman_char: str, good: Good):
        self.roman_char = roman_char
        self.good = good
        self.revealed = False

    def reveal(self) -> Good:
        """Turn the token face up and tell which good the city produces."""
        self.revealed = True
        return self.good

    def __repr__(self) -> str:
        return f"CityToken({self.roman_char!r}, {self.good.name!r})"

    def get_good(self) -> Good:
        """Return the good this token produces."""
        return self.good


class BonusMarker:
    """
    The marker of a province, showing the most valuable good produced there.
    """

    def __init__(self, good: Good):
        self.good = good
        self.coin_side = False

    @property
    def sestertii(self) -> int:
        """How many sestertii the marker pays when it is flipped."""
        return self.good.bonus_sestertii

    def __repr__(self) -> str:
        return f"BonusMarker({self.good.name!r})"
