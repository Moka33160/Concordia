"""
File: resource.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The goods of the game (brick, food, tool, wine and cloth).
"""


class Good:
    """One kind of good, as described by the ccd_good collection."""

    def __init__(self,
                 name: str,
                 value: int,
                 color: str,
                 bonus_sestertii: int,
                 build_cost_sestertii: int,
                 build_cost_goods: list[str] | None = None):
        """
        :param name: The good name, as the ORDB spells it.
        :param value: What orders the goods, from brick (3) to cloth (7).
        :param color: The colour the good is drawn in.
        :param bonus_sestertii: What the province bonus marker pays when
            it is flipped.
        :param build_cost_sestertii: The base price of a house in a city
            producing this good.
        :param build_cost_goods: The goods a house in such a city costs,
            from good_build_cost.
        """
        self.name = name
        self.value = value
        self.color = color
        self.bonus_sestertii = bonus_sestertii
        self.build_cost_sestertii = build_cost_sestertii
        self.build_cost_goods = list(build_cost_goods or [])

    def __repr__(self) -> str:
        return f"Good({self.name!r}, value={self.value})"
