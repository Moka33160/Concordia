"""
File: effects.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: Compares the game before and after a card, to find what it
             changed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from concordia.models.card import Card
    from concordia.models.city import City
    from concordia.models.colonist import Colonist
    from concordia.models.player import Player
    from concordia.state.game_state import GameState


@dataclass(frozen=True)
class Effect:
    """One thing a card did, as a player would say it."""

    @property
    def caption(self) -> str:
        """What to say about it in one line."""
        return ""


@dataclass(frozen=True)
class ColonistMoved(Effect):
    """A colonist that stands somewhere it did not stand before."""

    colonist: Colonist
    origin: Any
    destination: Any

    @property
    def caption(self) -> str:
        where = _name_of(self.destination)

        if self.origin is None:
            return f"places a {self.colonist.way} colonist at {where}"

        return f"moves a colonist to {where}"


@dataclass(frozen=True)
class HouseBuilt(Effect):
    """A house that was not in a city before."""

    city: City
    color: str

    @property
    def caption(self) -> str:
        return f"builds a house in {_name_of(self.city)}"


@dataclass(frozen=True)
class GoodsGained(Effect):
    """Units of one good that arrived in a storehouse."""

    player: Player
    good: str
    count: int

    @property
    def caption(self) -> str:
        return f"takes {self.count} {self.good}"


@dataclass(frozen=True)
class GoodsLost(Effect):
    """Units of one good that left a storehouse."""

    player: Player
    good: str
    count: int

    @property
    def caption(self) -> str:
        return f"pays {self.count} {self.good}"


@dataclass(frozen=True)
class CardBought(Effect):
    """A card that left the display and turned up in a hand."""

    player: Player
    card: Card

    @property
    def caption(self) -> str:
        return f"buys {self.card.name}"


@dataclass(frozen=True)
class MoneyChanged(Effect):
    """A purse that is not the size it was."""

    player: Player
    delta: int

    @property
    def caption(self) -> str:
        if self.delta < 0:
            return f"pays {-self.delta} sestertii"

        return f"takes {self.delta} sestertii"


def _name_of(place: Any) -> str:
    """What to call a place in a caption."""
    for attribute in ("display_name", "name"):
        found = getattr(place, attribute, None)

        if isinstance(found, str):
            return found.strip()

    return ""


def snapshot(game: GameState) -> dict:
    """
    Photograph everything a card is able to change.

    :param game: The game to photograph.
    :return: What `changes` subtracts.
    """
    board = game.board
    cities = [] if board is None else board.cities()
    market = game.market

    return {
        "positions": {
            colonist: colonist.position
            for player in game.players
            for colonist in player.colonists
        },
        "reserve": {
            player: tuple(player.storehouse_colonists)
            for player in game.players
        },
        "houses": {city: tuple(city.houses) for city in cities},
        "storehouse": {
            player: dict(player.storehouse) for player in game.players
        },
        "sestertii": {
            player: player.sestertii for player in game.players
        },
        "hands": {player: tuple(player.hand) for player in game.players},
        "discards": {
            player: tuple(player.discarded_cards) for player in game.players
        },
        "display": () if market is None else tuple(market.display),
    }


def untouched(before: dict, after: dict) -> bool:
    """
    Whether nothing at all moved between two photographs.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: True when the two are the same in every part.
    """
    return before == after


def changes(before: dict, after: dict) -> list[Effect]:
    """
    What happened between two photographs.

    :param before: The photograph taken before the card was played.
    :param after: The photograph taken after it.
    :return: What changed, empty when nothing did.
    """
    return [
        *_moves(before, after),
        *_houses(before, after),
        *_goods(before, after),
        *_purses(before, after),
        *_bought(before, after),
    ]


def _moves(before: dict, after: dict) -> list[Effect]:
    """
    The colonists standing somewhere new.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: One effect per piece that moved.
    """
    moved = []

    for colonist, position in after["positions"].items():
        was = before["positions"].get(colonist)

        if position is not None and position is not was:
            moved.append(ColonistMoved(colonist, was, position))

    return moved


def _houses(before: dict, after: dict) -> list[Effect]:
    """
    The houses that went up, one effect per house.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: One effect per house built.
    """
    built = []

    for city, houses in after["houses"].items():
        standing = list(before["houses"].get(city, ()))

        for color in houses:
            if color in standing:
                standing.remove(color)
            else:
                built.append(HouseBuilt(city, color))

    return built


def _goods(before: dict, after: dict) -> list[Effect]:
    """
    The goods that came and went, one effect per good per storehouse.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: The gains and the losses.
    """
    moved = []

    for player, storehouse in after["storehouse"].items():
        was = before["storehouse"].get(player, {})

        for good in sorted(set(storehouse) | set(was)):
            delta = storehouse.get(good, 0) - was.get(good, 0)

            if delta > 0:
                moved.append(GoodsGained(player, good, delta))
            elif delta < 0:
                moved.append(GoodsLost(player, good, -delta))

    return moved


def _purses(before: dict, after: dict) -> list[Effect]:
    """
    The purses that changed size.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: One effect per purse that moved.
    """
    return [
        MoneyChanged(player, sestertii - before["sestertii"].get(player, 0))
        for player, sestertii in after["sestertii"].items()
        if sestertii != before["sestertii"].get(player, 0)
    ]


def _bought(before: dict, after: dict) -> list[Effect]:
    """
    The cards that left the display for a hand.

    :param before: The earlier photograph.
    :param after: The later one.
    :return: One effect per card bought.
    """
    left_display = set(before["display"]) - set(after["display"])
    bought = []

    for player, hand in after["hands"].items():
        gained = set(hand) - set(before["hands"].get(player, ()))

        for card in hand:
            if card in gained and card in left_display:
                bought.append(CardBought(player, card))

    return bought


def caption_for(done: list[Effect]) -> str:
    """One line saying what a whole turn did."""
    said = [effect.caption for effect in done if effect.caption]

    return ", ".join(said)
