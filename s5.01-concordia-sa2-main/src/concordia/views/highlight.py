"""
File: highlight.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Highlights on the board what the current request can be answered
             with.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import (
    ChooseAmount, ChooseCity, ChooseColonist, ChooseDiscardCard, ChooseGood,
    ChooseMarketCard, ChooseOption, ChooseProvince, ChooseRoute,
    ChooseWay, Confirm,
)

if TYPE_CHECKING:
    from concordia.actions.requests import Request

# The requests answered by a button and not by clicking the board.
CONTROL_REQUESTS = (ChooseOption, Confirm, ChooseAmount, ChooseWay)


def cities_for(request: Request | None) -> set:
    """The cities to ring on the map."""
    if isinstance(request, ChooseCity):
        return set(request.options)

    if isinstance(request, ChooseColonist):
        return {
            colonist.city for colonist in request.options
            if colonist.city is not None
        }

    return set()


def routes_for(request: Request | None) -> set:
    """The routes to trace in gold on the map."""
    if isinstance(request, ChooseRoute):
        return set(request.options)

    if isinstance(request, ChooseColonist):
        return {
            colonist.route for colonist in request.options
            if colonist.route is not None
        }

    return set()


def route_steps(request: Request | None) -> dict:
    """What each route on offer costs to reach, in movement steps."""
    if not isinstance(request, ChooseRoute):
        return {}

    return {route: request.cost(route) for route in request.options}


def colonists_for(request: Request | None) -> set:
    """The colonists to ring on the map."""
    if isinstance(request, ChooseColonist):
        return set(request.options)

    return set()


def provinces_for(request: Request | None) -> set:
    """The province markers to ring on the map."""
    if isinstance(request, ChooseProvince):
        return set(request.options)

    return set()


def market_cards_for(request: Request | None) -> set:
    """The cards of the display to rim in gold."""
    if isinstance(request, ChooseMarketCard):
        return set(request.options)

    return set()


def goods_for(request: Request | None) -> set:
    """The storehouse chips to ring in the HUD."""
    if isinstance(request, ChooseGood):
        return set(request.options)

    return set()


def discards_for(request: Request | None) -> set:
    """The opponents' discarded cards to rim in gold."""
    if isinstance(request, ChooseDiscardCard):
        return set(request.options)

    return set()


def is_control(request: Request | None) -> bool:
    """Whether a request is answered by a button and not on the board."""
    return isinstance(request, CONTROL_REQUESTS)


def dims_the_map(request: Request | None) -> bool:
    """
    Whether the map should recede behind the request.

    A province is left out: it is told apart by the tint of its ground, which
    fading the map would wash away.
    """
    return bool(
        cities_for(request) or colonists_for(request) or routes_for(request)
    )
