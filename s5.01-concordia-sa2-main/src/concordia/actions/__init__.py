"""
File: __init__.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: One module per personality card, looked up by the name of the
             card.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from concordia.actions import (architect, colonist, consul, prefect, diplomat,
                               tribune, specialist, senator, mercator)

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext
    from concordia.actions.requests import Flow

# The five MINERVA specialists share one action, the good is read on the card.
SPECIALISTS = ("VINTNER", "FARMER", "WEAVER", "SMITH", "MASON")

ACTIONS: dict[str, Callable[[ActionContext], Flow]] = {
    "ARCHITECT": architect.play,
    "COLONIST": colonist.play,
    "CONSUL": consul.play,
    "DIPLOMAT": diplomat.play,
    "MERCATOR": mercator.play,
    "PREFECT": prefect.play,
    "SENATOR": senator.play,
    "TRIBUNE": tribune.play,
    **{name: specialist.play for name in SPECIALISTS},
}

PLAYABILITY: dict[str, Callable[[ActionContext], bool]] = {
    "ARCHITECT": architect.is_playable,
    "COLONIST": colonist.is_playable,
    "CONSUL": consul.is_playable,
    "DIPLOMAT": diplomat.is_playable,
    "MERCATOR": mercator.is_playable,
    "PREFECT": prefect.is_playable,
    "SENATOR": senator.is_playable,
    "TRIBUNE": tribune.is_playable,
    **{name: specialist.is_playable for name in SPECIALISTS},
}
