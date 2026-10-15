"""
File: architect.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The ARCHITECT action: move the colonists, then build the houses.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions.requests import (
    ChooseCity, ChooseColonist, ChooseRoute, Flow,
)
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.route import Route

if TYPE_CHECKING:
    from concordia.actions.context import ActionContext


def is_playable(ctx: ActionContext) -> bool:
    """Whether the architect has anything to do."""
    if not movable_colonists(ctx):
        return False

    return bool(any_step(ctx) or buildable_cities(ctx))


def play(ctx: ActionContext) -> Flow:
    """Move the colonists, then build wherever they have ended up."""
    if not is_playable(ctx):
        return False

    before = table_before(ctx)

    try:
        yield from move_colonists(ctx)
        yield from build_houses(ctx)
    except GeneratorExit:
        put_back(ctx, before)
        raise

    return True


# --- Giving the card up ---

def table_before(ctx: ActionContext) -> dict:
    """
    Note everything the architect can change, before it changes anything.
    """
    board = ctx.game_state.board

    return {
        "standing": {
            colonist: colonist.position for colonist in ctx.player.colonists
        },
        "pieces": {
            place: list(place.colonists)
            for place in (*board.cities(), *board.routes)
        },
        "houses": {
            city: list(city.houses) for city in board.cities()
        },
        "supply": ctx.player.houses,
        "sestertii": ctx.player.sestertii,
        "storehouse": dict(ctx.player.storehouse),
    }


def put_back(ctx: ActionContext, before: dict) -> None:
    """
    Put the game back to what `table_before` noted down.

    :param ctx: The card, the player and the game.
    :param before: What the game looked like before the card was played.
    """
    for colonist, position in before["standing"].items():
        colonist.position = position

    for place, standing in before["pieces"].items():
        place.colonists[:] = standing

    for city, houses in before["houses"].items():
        city.houses[:] = houses

    ctx.player.houses = before["supply"]
    ctx.player.sestertii = before["sestertii"]
    ctx.player.storehouse.clear()
    ctx.player.storehouse.update(before["storehouse"])


# --- Moving ---

def move_colonists(ctx: ActionContext) -> Flow:
    """
    Spend the movement steps, one colonist and one route at a time.

    :param ctx: The card, the player and the game.
    """
    remaining = available_colonist(ctx)

    while remaining > 0:
        within_reach = {
            colonist: destinations(ctx, colonist, remaining)
            for colonist in movable_colonists(ctx)
        }
        movers = tuple(
            colonist for colonist, routes in within_reach.items() if routes
        )

        if not movers:
            return

        colonist = yield ChooseColonist(
            f"Which colonist moves? ({remaining} step(s) left, "
            f"or skip to start building)",
            options=movers, optional=True,
        )

        if colonist is None:
            return

        reached = within_reach[colonist]
        route = yield ChooseRoute(
            step_prompt(colonist, remaining, reached),
            options=tuple(reached), steps=tuple(reached.values()),
        )

        colonist.place(route)
        remaining -= reached[route]


def step_prompt(colonist: Colonist, remaining: int,
                reached: dict[Route, int]) -> str:
    """
    Ask where a colonist goes, and say what the far ones cost.

    :param colonist: The colonist being moved.
    :param remaining: How many steps are still in hand.
    :param reached: What each route on offer costs in steps.
    :return: The line the choice bar shows.
    """
    line = f"Where does the {colonist.way} colonist go? ({remaining} step(s)"

    if any(cost > 1 for cost in reached.values()):
        return f"{line} left, a marked route spends that many)"

    return f"{line} left)"


def available_colonist(ctx: ActionContext) -> int:
    """Count the colonists that are already placed on the board."""
    return len(movable_colonists(ctx))


def movable_colonists(ctx: ActionContext) -> list[Colonist]:
    """The player's colonists standing on the board."""
    return [
        colonist for colonist in ctx.player.colonists if colonist.is_placed
    ]


def is_free(route: Route) -> bool:
    """Whether a colonist may come to rest on a route."""
    return not route.colonists


def onward_from(ctx: ActionContext, position, way: str) -> list[Route]:
    """
    The routes of one way lying one step on from somewhere.

    :param ctx: The card, the player and the game.
    :param position: The city or route being left.
    :param way: The way the colonist travels by.
    :return: The routes one step on.
    """
    board = ctx.game_state.board

    if isinstance(position, Route):
        return board.routes_next_to(position, way)

    return board.routes_at(position, way)


def destinations(ctx: ActionContext, colonist: Colonist,
                 steps: int = 1) -> dict[Route, int]:
    """
    Everywhere a colonist could come to rest, and what each costs.

    :param ctx: The card, the player and the game.
    :param colonist: The colonist to move.
    :param steps: How many movement steps are still in hand.
    :return: The routes it may end on, each mapped to the steps it spends,
        empty when it is boxed in or has no step left.
    """
    if colonist.position is None or steps < 1:
        return {}

    reached: dict[Route, int] = {}
    walked = {colonist.position}
    edge = [colonist.position]

    for distance in range(1, steps + 1):
        onward = []

        for position in edge:
            for route in onward_from(ctx, position, colonist.way):
                if route in walked:
                    continue

                walked.add(route)
                onward.append(route)

                if is_free(route):
                    reached[route] = distance

        edge = onward

    return reached


def any_step(ctx: ActionContext) -> bool:
    """Whether any colonist of the player has a move it could make."""
    allowance = available_colonist(ctx)

    return any(
        destinations(ctx, colonist, allowance)
        for colonist in movable_colonists(ctx)
    )


# --- Building ---

def build_houses(ctx: ActionContext) -> Flow:
    """Build in as many of the reached cities as the player will pay for."""
    while True:
        sites = tuple(buildable_cities(ctx))

        if not sites:
            return

        city = yield ChooseCity(
            build_prompt(sites), options=sites, optional=True,
        )

        if city is None:
            return

        build_house(ctx, city)


def build_prompt(sites: tuple[City, ...]) -> str:
    """Read out what each city on offer would cost to build in."""
    priced = []

    for city in sites:
        price, materials = get_city_price(city)
        priced.append(
            f"{city.display_name} {price}s + {', '.join(materials)}"
        )

    return f"Build a house? {' · '.join(priced)}, or skip to finish."


def adjacent_cities(ctx: ActionContext) -> list[City]:
    """Every city one of the player's colonists is standing next to."""
    found: list[City] = []

    for colonist in movable_colonists(ctx):
        reached = (
            colonist.route.cities if colonist.route is not None
            else (colonist.city,)
        )
        for city in reached:
            if city is not None and city not in found:
                found.append(city)

    return found


def buildable_cities(ctx: ActionContext) -> list[City]:
    """The cities the player could build in right now."""
    return [city for city in adjacent_cities(ctx) if can_build(ctx, city)]


def get_city_price(city: City) -> tuple[int, list[str]]:
    """Calculate the cost of building a house in a city."""
    city_good = city.get_token().get_good()
    price = city_good.build_cost_sestertii * (city.get_nb_house() + 1)

    return price, list(city_good.build_cost_goods)


def can_build(ctx: ActionContext, city: City) -> bool:
    """
    Whether a house can be built in a city right now.

    :param ctx: The card, the player and the game.
    :param city: The city the house would go in.
    :return: True when the city has room for one more of the player's houses,
        the player has one left to build, and the storehouse and purse can pay
        for it.
    """
    if city is ctx.game_state.board.capital:
        return False

    if city.get_token() is None or city.is_full:
        return False

    if ctx.player.color in city.houses:
        return False

    if ctx.player.houses <= 0:
        return False

    price, materials = get_city_price(city)

    return (
        ctx.player.sestertii >= price
        and ctx.player.has_enough_materials(materials)
    )


def build_house(ctx: ActionContext, city: City) -> bool:
    """
    Build a house for the player in a city, and pay for it.

    :param ctx: The card, the player and the game.
    :param city: City where the house will be built.
    :return: True if the house was built, False otherwise.
    """
    if not can_build(ctx, city):
        return False

    price, materials = get_city_price(city)

    if not ctx.player.pay_city_cost(price, materials):
        return False

    city.add_house(ctx.player.color)
    ctx.player.houses -= 1

    return True
