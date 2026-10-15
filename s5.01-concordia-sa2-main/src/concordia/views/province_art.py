"""
File: province_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: The area a province covers on the map, and the tint it is filled
             with.
"""
from __future__ import annotations

import math

from concordia.views.palette import (
    MAP_BACKGROUND, PROVINCE_EDGE, PROVINCE_TINTS, PROVINCE_WASH, blend,
)

Point = tuple[float, float]

# How many points a city is ringed with before the hull is taken.
GROUND_STEPS = 24


def tint(index: int) -> str:
    """The hue a province is washed in, by its place on the board."""
    return PROVINCE_TINTS[index % len(PROVINCE_TINTS)]


def wash(index: int) -> str:
    """The colour a province's ground comes out as on bare parchment."""
    return blend(MAP_BACKGROUND, tint(index), PROVINCE_WASH)


def edge(index: int) -> str:
    """The colour the line around a province's ground is drawn in."""
    return blend(MAP_BACKGROUND, tint(index), PROVINCE_EDGE)


def ground(points: list[Point], margin: float,
           steps: int = GROUND_STEPS) -> list[Point]:
    """
    The area the points of a province sit in, grown by a margin.

    :param points: The points of the province: its cities and its bonus
        marker, in canvas coordinates.
    :param margin: How far outside them the area reaches, so a city is not on
        the edge of it.
    :param steps: How many points each of them is ringed with, so how round
        the corners are.
    :return: The area as the points of a closed polygon, empty when there is
        nothing.
    """
    if not points:
        return []

    cloud = [
        (x + margin * math.cos(angle), y + margin * math.sin(angle))
        for x, y in points
        for angle in (2 * math.pi * step / steps for step in range(steps))
    ]
    return _hull(cloud)


def regions(points: list[Point], margin: float, link: float,
            steps: int = GROUND_STEPS) -> list[list[Point]]:
    """
    The areas a province covers, one per part of it.

    :param points: The points of the province: its cities and its bonus
        marker, in canvas coordinates.
    :param margin: How far outside them an area reaches.
    :param link: The longest gap that still counts as one part of the
        province, so two cities across a sea are not drawn together.
    :param steps: How many points each of them is ringed with.
    :return: One polygon per part, in the order the points came in.
    """
    return [
        ground(group, margin, steps) for group in _groups(points, link)
    ]


def _groups(points: list[Point], link: float) -> list[list[Point]]:
    """
    Group points into the parts of the map they actually sit on.

    :param points: The points to group.
    :param link: The longest hop between two points of one part.
    :return: The groups, none of them empty.
    """
    groups: list[list[Point]] = []

    for point in points:
        near = [
            group for group in groups
            if any(math.dist(point, other) <= link for other in group)
        ]
        joined = [point] + [other for group in near for other in group]
        groups = [
            group for group in groups
            if all(group is not reached for reached in near)
        ]
        groups.append(joined)

    return groups


def _cross(origin: Point, first: Point, second: Point) -> float:
    """
    Which side of `origin`->`first` the point `second` falls on.

    :param origin: The start of the line.
    :param first: The end of the line.
    :param second: The point to place against it.
    :return: Positive when the three turn counter-clockwise, negative when
        they turn clockwise, zero when they are in line.
    """
    return ((first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0]))


def _hull(points: list[Point]) -> list[Point]:
    """The convex hull of a cloud of points, by Andrew's monotone chain."""
    ordered = sorted(set(points))

    if len(ordered) < 3:
        return ordered

    def chain(sequence: list[Point]) -> list[Point]:
        """One side of the hull, dropping every corner that turns in."""
        side: list[Point] = []

        for point in sequence:
            while len(side) >= 2 and _cross(side[-2], side[-1], point) <= 0:
                side.pop()
            side.append(point)

        return side[:-1]

    return chain(ordered) + chain(ordered[::-1])
