"""
File: colonist.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The COLONIST action: take the sestertii, or pay one food and one
             tool to place a colonist.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import (
    ChooseCity, ChooseOption, ChooseWay, Flow, Option,
)
from concordia.models.city import City
from concordia.rules import COLONIST_COST

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext

TAKE_SESTERTII = Option("sestertii", "Take the sestertii")
PLACE_COLONIST = Option("place", "Place a colonist")


def is_playable(ctx: ActionContext) -> bool:
    """Whether the colonist can be played."""
    return True


def play(ctx: ActionContext) -> Flow:
    """Take the sestertii, or place colonists and pay for each of them."""
    choices = [TAKE_SESTERTII]

    if can_place(ctx):
        choices.append(PLACE_COLONIST)

    chosen = yield ChooseOption(
        "What does the Colonist do?", options=tuple(choices),
    )

    if chosen is TAKE_SESTERTII:
        take_sestertii(ctx)
        return True

    yield from place_colonists(ctx)
    return True


def place_colonists(ctx: ActionContext) -> Flow:
    """Place as many colonists as the reserve and the storehouse allow."""
    while can_place(ctx):
        way = yield ChooseWay(
            "Which colonist do you send? (or stop placing)",
            options=tuple(available_ways(ctx)), optional=True,
        )

        if way is None:
            return

        place = yield ChooseCity(
            "Where does it go?", options=tuple(available_places(ctx)),
        )

        place_colonist(ctx, way, place)


def can_place(ctx: ActionContext) -> bool:
    """
    Whether a colonist can be placed at all: one is in reserve, somewhere
    takes it, and the storehouse can pay for it.
    """
    storehouse = ctx.player.storehouse

    return (
        bool(available_ways(ctx))
        and bool(available_places(ctx))
        and all(storehouse.get(good, 0) >= 1 for good in COLONIST_COST)
    )


def available_ways(ctx: ActionContext) -> list[str]:
    """The ways the player still has a colonist in reserve for."""
    return sorted({
        colonist.way for colonist in ctx.player.storehouse_colonists
    })


def available_places(ctx: ActionContext) -> list[City]:
    """
    The cities a colonist can be placed on: the capital, and every city the
    player owns a house in.
    """
    board = ctx.game_state.board
    places = [board.capital]

    for province in board.provinces:
        for city in province.cities:
            if ctx.player.color in city.houses and city not in places:
                places.append(city)

    return places


def take_sestertii(ctx: ActionContext) -> None:
    """
    Pay the player 5 sestertii, plus one per colonist already on the board.
    """
    ctx.player.receive_sestertii(5 + len(ctx.player.colonists))


def place_colonist(ctx: ActionContext, way: str, place: City) -> bool:
    """
    Put a colonist of the given way on a city, and pay for it.

    :param ctx: The card, the player and the game.
    :param way: The way the colonist travels by.
    :param place: The city it starts on.
    :return: True when a colonist was placed and paid for.
    """
    player = ctx.player

    if player.place_colonist(way, place) is None:
        return False

    for good in COLONIST_COST:
        player.storehouse[good] -= 1

    return True
