"""
File: svg_art.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Reads the small SVG pieces of assets/pions into a Pillow image.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Pillow does the rasterising.
try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
except ImportError:  # pragma: no cover - exercised by the CI image
    Image = ImageChops = ImageDraw = ImageFilter = None

# The SVG path commands. Splitting on any letter would cut "1e-3" in half.
COMMANDS = "MmZzLlHhVvCcSsQqTtAa"

_GROUP = re.compile(f"([{COMMANDS}])([^{COMMANDS}]*)")
_NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_VIEWBOX = re.compile(r'viewBox\s*=\s*"([^"]*)"')
_PATH = re.compile(r"<path\b([^>]*)>")
_ATTRIBUTE = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')

# How many straight steps a curve is cut into.
CURVE_STEPS = 12

# The mask is drawn this much bigger, then scaled back down.
SUPERSAMPLE = 4

# How far the keyline around a piece reaches, in final pixels.
OUTLINE_WIDTH = 1


@dataclass(frozen=True)
class Shape:
    """One `<path>` of an icon: its outline, and how the file paints it."""

    subpaths: tuple[tuple[tuple[float, float], ...], ...]
    width: float = 0.0

    @property
    def is_stroked(self) -> bool:
        """Whether the path is a line of a given thickness, not a solid."""
        return self.width > 0


@dataclass(frozen=True)
class Glyph:
    """An icon: the box the file draws in, and the paths drawn in it."""

    width: float
    height: float
    shapes: tuple[Shape, ...]

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """
        The box the icon actually draws in, rather than the one it declares.
        """
        edges = [
            (x - shape.width / 2, y - shape.width / 2,
             x + shape.width / 2, y + shape.width / 2)
            for shape in self.shapes
            for subpath in shape.subpaths
            for x, y in subpath
        ]

        if not edges:
            return 0.0, 0.0, self.width, self.height

        return (
            min(edge[0] for edge in edges),
            min(edge[1] for edge in edges),
            max(edge[2] for edge in edges),
            max(edge[3] for edge in edges),
        )


# --- Reading ---

def flatten(data: str) -> tuple[tuple[tuple[float, float], ...], ...]:
    """
    Cut a path's `d` attribute into polylines, one per subpath.

    :param data: The `d` attribute, as the file spells it.
    :return: One tuple of points per subpath, in the file's own units.
    """
    subpaths: list[tuple[tuple[float, float], ...]] = []
    points: list[tuple[float, float]] = []
    here = start = (0.0, 0.0)
    mirror: tuple[float, float] | None = None

    def close(shut: bool) -> None:
        """Bank the subpath being walked, shutting it when asked."""
        nonlocal points
        if len(points) > 1:
            subpaths.append(tuple(points + [start] if shut else points))
        points = []

    for letter, numbers in _GROUP.findall(data):
        values = [float(number) for number in _NUMBER.findall(numbers)]

        if letter in "Zz":
            close(shut=True)
            here = start
            mirror = None
            continue

        for step in _steps(letter, values):
            moved, here, mirror = _walk(letter, step, here, mirror)

            if letter in "Mm":
                close(shut=False)
                start = here
                points = [here]
                # After the first pair, a moveto is a lineto.
                letter = "L" if letter == "M" else "l"
            else:
                points.extend(moved)

    close(shut=False)
    return tuple(subpaths)


def read_glyph(path: Path) -> Glyph | None:
    """Read an icon off disk."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None

    return parse_glyph(source)


def parse_glyph(source: str) -> Glyph:
    """Read an icon out of the text of an SVG file."""
    declared = _VIEWBOX.search(source)
    box = _NUMBER.findall(declared.group(1)) if declared else []
    width, height = (
        (float(box[2]), float(box[3])) if len(box) == 4 else (0.0, 0.0)
    )

    shapes = []
    for attributes in _PATH.findall(source):
        found = dict(_ATTRIBUTE.findall(attributes))
        if "d" not in found:
            continue

        # A path with no stroke is filled; the plane is drawn as a line.
        stroked = found.get("stroke", "none") != "none"
        shapes.append(Shape(
            flatten(found["d"]),
            float(found.get("stroke-width", 1)) if stroked else 0.0,
        ))

    return Glyph(width, height, tuple(shapes))


# --- Drawing ---

def render(glyph: Glyph, box_width: float, box_height: float, fill: str,
           outline: str | None = None) -> Any:
    """
    Draw an icon at a size, in a colour, with a keyline around it.

    :param glyph: The icon to draw.
    :param box_width: The width the icon has to fit in.
    :param box_height: The height it has to fit in.
    :param fill: The colour to pour through it.
    :param outline: The colour of the keyline around it, None for none.
    :return: The RGBA picture, None when Pillow is missing.
    """
    if Image is None:
        return None

    box = (max(1, round(box_width)), max(1, round(box_height)))
    big = (box[0] * SUPERSAMPLE, box[1] * SUPERSAMPLE)

    # The keyline is drawn around the icon, so the icon gets a smaller box.
    reach = OUTLINE_WIDTH * SUPERSAMPLE if outline is not None else 0
    coverage = Image.new("L", big, 0)
    coverage.paste(
        mask(glyph, max(1, big[0] - reach * 2), max(1, big[1] - reach * 2)),
        (reach, reach),
    )

    picture = _painted(big, outline or fill, _spread(coverage, outline))
    picture.alpha_composite(_painted(big, fill, coverage))
    return picture.resize(box, Image.LANCZOS)


def mask(glyph: Glyph, width: int, height: int) -> Any:
    """
    The coverage of an icon drawn at a size: white where it draws.

    :param glyph: The icon to draw.
    :param width: The width to draw it at.
    :param height: The height to draw it at.
    :return: The mask, as a Pillow "L" picture.
    """
    coverage = Image.new("L", (width, height), 0)
    scale, offset = _placement(glyph, width, height)

    for shape in glyph.shapes:
        placed = [
            [_place(point, scale, offset) for point in subpath]
            for subpath in shape.subpaths if len(subpath) > 1
        ]

        if shape.is_stroked:
            _stroke(coverage, placed, max(1, round(shape.width * scale)))
            continue

        for subpath in placed:
            layer = Image.new("L", (width, height), 0)
            ImageDraw.Draw(layer).polygon(subpath, fill=255)
            coverage = ImageChops.difference(coverage, layer)

    return coverage


def _placement(glyph: Glyph, width: int,
               height: int) -> tuple[float, tuple[float, float]]:
    """
    How the icon's own box is laid into the box asked for.

    :param glyph: The icon being drawn.
    :param width: The width to fit it into.
    :param height: The height to fit it into.
    :return: The scale to draw at, and the (x, y) to shift by after it.
    """
    left, top, right, bottom = glyph.bounds
    span_width = max(right - left, 1e-6)
    span_height = max(bottom - top, 1e-6)
    scale = min(width / span_width, height / span_height)

    return scale, (
        (width - span_width * scale) / 2 - left * scale,
        (height - span_height * scale) / 2 - top * scale,
    )


def _place(point: tuple[float, float], scale: float,
           offset: tuple[float, float]) -> tuple[float, float]:
    """Move one point of the file's own space into the picture's."""
    return point[0] * scale + offset[0], point[1] * scale + offset[1]


def _stroke(coverage: Any, subpaths: list, width: int) -> None:
    """
    Lay a stroked path into a mask, joints rounded off.

    :param coverage: The mask to draw into.
    :param subpaths: The polylines, already placed in the picture.
    :param width: The thickness to draw them at.
    """
    pen = ImageDraw.Draw(coverage)

    for subpath in subpaths:
        pen.line(subpath, fill=255, width=width, joint="curve")

        # joint rounds the corners but leaves the ends square, and the file
        # wants round caps.
        for x, y in (subpath[0], subpath[-1]):
            radius = width / 2
            pen.ellipse(
                (x - radius, y - radius, x + radius, y + radius), fill=255
            )


def _spread(coverage: Any, outline: str | None) -> Any:
    """
    Grow a mask by the keyline's width, for the edge drawn under it.

    :param coverage: The icon's own coverage.
    :param outline: The keyline's colour, None when there is none.
    :return: The grown mask, or `coverage` itself when nothing is grown.
    """
    if outline is None:
        return coverage

    reach = OUTLINE_WIDTH * SUPERSAMPLE
    return coverage.filter(ImageFilter.MaxFilter(reach * 2 + 1))


def _painted(size: tuple[int, int], color: str, coverage: Any) -> Any:
    """
    A flat colour, showing only where the mask allows it.

    :param size: The size of the picture.
    :param color: The colour to lay down.
    :param coverage: The mask cutting it back.
    :return: The RGBA picture.
    """
    picture = Image.new("RGBA", size, color)
    picture.putalpha(coverage)
    return picture


# --- Walking a path ---

# How many numbers each command eats at a time.
RUN = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2,
       "A": 7}


def _steps(letter: str, values: list[float]) -> list[list[float]]:
    """
    Cut a command's numbers into the runs it is really several of.

    :param letter: The command, in either case.
    :param values: Every number that followed it.
    :return: One list of numbers per run of the command.
    """
    run = RUN.get(letter.upper(), 2)
    return [values[n:n + run] for n in range(0, len(values), run)
            if len(values[n:n + run]) == run]


def _walk(letter: str, step: list[float], here: tuple[float, float],
          mirror: tuple[float, float] | None
          ) -> tuple[list, tuple[float, float], tuple[float, float] | None]:
    """
    Take one run of one command, from wherever the pen has got to.

    :param letter: The command, uppercase absolute and lowercase relative.
    :param step: The numbers of this run.
    :param here: Where the pen is.
    :param mirror: The point a smooth curve reflects its control through, None
        when the last command was not a curve.
    :return: The points walked over, where the pen ends up, and the mirror the
        next smooth curve would use.
    """
    relative = letter.islower()
    shift = here if relative else (0.0, 0.0)
    command = letter.upper()

    if command in ("M", "L"):
        end = (step[0] + shift[0], step[1] + shift[1])
        return [end], end, None

    if command == "H":
        end = (step[0] + shift[0], here[1])
        return [end], end, None

    if command == "V":
        end = (here[0], step[0] + shift[1])
        return [end], end, None

    if command == "C":
        first = (step[0] + shift[0], step[1] + shift[1])
        second = (step[2] + shift[0], step[3] + shift[1])
        end = (step[4] + shift[0], step[5] + shift[1])
        return _cubic(here, first, second, end), end, second

    if command == "S":
        first = mirror or here
        first = (2 * here[0] - first[0], 2 * here[1] - first[1])
        second = (step[0] + shift[0], step[1] + shift[1])
        end = (step[2] + shift[0], step[3] + shift[1])
        return _cubic(here, first, second, end), end, second

    # No file of assets/pions uses a quadratic or an arc, so a straight line
    # will do.
    end = (step[-2] + shift[0], step[-1] + shift[1])
    return [end], end, None


def _cubic(start: tuple[float, float], first: tuple[float, float],
           second: tuple[float, float],
           end: tuple[float, float]) -> list[tuple[float, float]]:
    """
    Cut a cubic bezier into straight steps.

    :param start: Where the curve leaves.
    :param first: The control point it leaves along.
    :param second: The control point it arrives along.
    :param end: Where it arrives.
    :return: The points of the curve, the first one left off as the pen is
        standing on it already.
    """
    walked = []

    for index in range(1, CURVE_STEPS + 1):
        t = index / CURVE_STEPS
        rest = 1 - t
        walked.append(tuple(
            rest ** 3 * start[axis]
            + 3 * rest ** 2 * t * first[axis]
            + 3 * rest * t ** 2 * second[axis]
            + t ** 3 * end[axis]
            for axis in (0, 1)
        ))

    return walked
