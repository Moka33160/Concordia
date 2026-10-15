"""
File: consul.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The CONSUL action: buy one card of the display, paying only the
             goods printed on it.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions import senator
from concordia.actions.requests import Flow

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext

MAX_PURCHASES = 1
SLOT_SURCHARGE = False


def is_playable(ctx: ActionContext) -> bool:
    """Whether the consul has a card in reach."""
    return bool(senator.affordable_cards(ctx, SLOT_SURCHARGE))


def play(ctx: ActionContext) -> Flow:
    """Buy one card of the display, at the price printed on it."""
    return (yield from senator.purchase_cards(
        ctx, MAX_PURCHASES, slot_surcharge=SLOT_SURCHARGE
    ))
