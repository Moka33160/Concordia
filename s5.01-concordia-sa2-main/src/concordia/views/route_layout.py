"""
File: route_layout.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The geometry the routes of the map are drawn with.
"""
import math

Point = tuple[float, float]

# The order the ways of one pair are drawn in, across the axis.
WAY_ORDER = ("land", "sea", "air")

# How far the outer way of a pair bulges off the straight line, in pixels.
WAY_FAN_OFFSET = 8.0

# How many segments a curve is drawn with.
CURVE_STEPS = 16


def fan_offsets(count: int) -> tuple[float, ...]:
    """Spread `count` ways evenly across the axis joining their two cities."""
    if count <= 1:
        return (0.0,)
    step = 2 * WAY_FAN_OFFSET / (count - 1)
    middle = (count - 1) / 2
    return tuple((index - middle) * step for index in range(count))


def curve_points(
        start: Point, end: Point, offset: float, steps: int = CURVE_STEPS
) -> list[Point]:
    """
    The points of the curve one way is drawn along, bulging `offset` off its
    axis.

    :param start: The position of the first city, in canvas pixels.
    :param end: The position of the second city, in canvas pixels.
    :param offset: How far the top of the curve stands off the midpoint,
        perpendicular to the axis. The sign says which side it bulges to, and
        zero draws it straight.
    :param steps: How many segments to sample the curve over.
    :return: The points of the curve, first on `start` and last on `end`.
    """
    span_x, span_y = end[0] - start[0], end[1] - start[1]
    length = math.hypot(span_x, span_y)
    if offset == 0 or length == 0:
        return [start, end]

    # The control point is twice the offset out: a quadratic Bezier only
    # reaches halfway.
    normal_x, normal_y = -span_y / length, span_x / length
    control = (
        (start[0] + end[0]) / 2 + 2 * offset * normal_x,
        (start[1] + end[1]) / 2 + 2 * offset * normal_y,
    )
    return [
        _bezier(start, control, end, step / steps)
        for step in range(steps + 1)
    ]


def group_routes(routes) -> list[list[tuple]]:
    """
    Gather the routes joining the same two cities, ready to be fanned out.
    """
    groups: dict[frozenset, list[tuple]] = {}
    for route in routes:
        city_a, city_b, _kind = route
        groups.setdefault(frozenset((city_a, city_b)), []).append(route)
    return [sorted(group, key=_way_rank) for group in groups.values()]


def route_curves(routes, points: dict) -> list[tuple]:
    """
    The line every route of the board is drawn along.

    :param routes: The board's routes, as (city, city, kind) triples.
    :param points: The position of each city on the canvas, keyed by city.
    :return: One (route, points) pair per route, so a caller can find the line
        of a given route to place a colonist on it or to catch a click.
    """
    laid = []
    for group in group_routes(routes):
        for route, offset in zip(group, fan_offsets(len(group))):
            city_a, city_b, _kind = route
            laid.append((
                route,
                curve_points(points[city_a], points[city_b], offset),
            ))
    return laid


def route_polylines(routes, points: dict) -> list[tuple[str, list[Point]]]:
    """
    The same lines, but named by the way instead of the route.

    :param routes: The board's routes, as (city, city, kind) triples.
    :param points: The position of each city on the canvas, keyed by city.
    :return: One (way, points) pair per route, the way giving the colour of
        the line.
    """
    return [
        (route[2], polyline)
        for route, polyline in route_curves(routes, points)
    ]


def midpoint(polyline: list[Point]) -> Point:
    """The middle of a drawn route, where its pieces stand."""
    half = len(polyline) // 2

    if len(polyline) % 2:
        return polyline[half]

    left, right = polyline[half - 1], polyline[half]
    return (left[0] + right[0]) / 2, (left[1] + right[1]) / 2


def distance_to(point: Point, polyline: list[Point]) -> float:
    """
    How far a point lies from the nearest part of a drawn route.

    :param point: The point to measure from, in canvas pixels.
    :param polyline: The points the route is drawn along.
    :return: The distance in pixels to the closest point of the line.
    """
    return min(
        _distance_to_segment(point, start, end)
        for start, end in zip(polyline, polyline[1:])
    )


def _distance_to_segment(point: Point, start: Point, end: Point) -> float:
    """The distance from a point to one segment of a line."""
    span_x, span_y = end[0] - start[0], end[1] - start[1]
    span = span_x ** 2 + span_y ** 2

    if span == 0:
        return math.hypot(point[0] - start[0], point[1] - start[1])

    along = (
        (point[0] - start[0]) * span_x + (point[1] - start[1]) * span_y
    ) / span
    along = max(0.0, min(1.0, along))

    return math.hypot(
        point[0] - (start[0] + along * span_x),
        point[1] - (start[1] + along * span_y),
    )


def _way_rank(route: tuple) -> int:
    """Where a route's way falls in the drawing order, unknown ways last."""
    kind = route[2]
    return WAY_ORDER.index(kind) if kind in WAY_ORDER else len(WAY_ORDER)


def _bezier(start: Point, control: Point, end: Point, along: float) -> Point:
    """One point of the quadratic Bezier through `start` and `end`."""
    left = (1 - along) ** 2
    middle = 2 * along * (1 - along)
    right = along ** 2
    return (
        left * start[0] + middle * control[0] + right * end[0],
        left * start[1] + middle * control[1] + right * end[1],
    )
