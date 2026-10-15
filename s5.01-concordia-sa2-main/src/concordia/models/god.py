"""
File: god.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026

Description: Model representing a god entity in the Concordia game domain.
"""


class God:
    """Model representing a god entity in the Concordia game domain."""

    def __init__(self, name: str, significance: str, reward: str,
                 example: str, vp_bonus: int):
        """
        Initialize a God instance.

        :param name: The name of the god.
        :param significance: The significance or description of the god.
        :param reward: The reward associated with the god.
        :param example: An example or illustration related to the god.
        :param vp_bonus: The victory points bonus associated with the god.
        """
        self.name = name
        self.significance = significance
        self.reward = reward
        self.example = example
        self.victory_points = vp_bonus

    def __repr__(self) -> str:
        return (
            f"God({self.name!r}, significance={self.significance!r}, "
            f"reward={self.reward!r}, example={self.example!r}, "
            f"victory_points={self.victory_points!r})"
        )
