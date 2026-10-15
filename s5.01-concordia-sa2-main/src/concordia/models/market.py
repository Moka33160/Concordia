"""
File: market.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The card market, holding the decks of personality cards and their
             display.
"""
import random
from dataclasses import dataclass

from concordia.models.card import Card

DEFAULT_DISPLAY_SIZE = 7


@dataclass(frozen=True)
class DisplaySlot:
    """One position of the display area, as ccd_display_area holds it."""

    position: int
    any_good_required: bool
    good: str | None = None
    n_goods: int | None = None


class CardMarket:
    """The card market: the deck stack and the cards displayed for sale."""

    def __init__(self, slots: list[DisplaySlot] | None = None):
        self._decks: dict[int, list[Card]] = {}
        self.stack: list[Card] = []
        self.display: list[Card] = []
        self.aside: Card | None = None
        self.slots: list[DisplaySlot] = list(slots or [])

    @property
    def display_size(self) -> int:
        """How many cards are laid out for sale."""
        return len(self.slots) or DEFAULT_DISPLAY_SIZE

    def slot_from(self, card: Card) -> DisplaySlot | None:
        """The display slot occupied by a card."""
        try:
            index = self.display.index(card)
        except ValueError:
            return None
        return self.slot_at(index + 1)

    def slot_at(self, position: int) -> DisplaySlot | None:
        """The display slot sitting at a position."""
        for slot in self.slots:
            if slot.position == position:
                return slot
        return None

    def add_card(self, card: Card) -> None:
        """File a card under its deck number."""
        self._decks.setdefault(card.deck_number, []).append(card)

    def set_aside(self, card: Card) -> None:
        """Set a card aside, out of the stack (the CONCORDIA card)."""
        self.aside = card

    def prepare_stack(self, nb_players: int, rng: random.Random) -> None:
        """
        Build the draw stack and deal the first display.

        :param nb_players: The number of players, decks above it are dropped.
        :param rng: The random generator used to shuffle, kept injectable for
            tests.
        """
        self.stack = []
        deck_numbers = sorted(
            number for number in self._decks if number <= nb_players
        )
        for deck_number in deck_numbers:
            deck_cards = list(self._decks[deck_number])
            rng.shuffle(deck_cards)
            self.stack.extend(deck_cards)
        self.display = self.draw(self.display_size)

    def draw(self, count: int) -> list[Card]:
        """Take cards off the top of the stack."""
        drawn, self.stack = self.stack[:count], self.stack[count:]
        return drawn

    def is_stack_empty(self) -> bool:
        """Check if the stack is empty."""
        return len(self.stack) == 0

    def is_display_empty(self) -> bool:
        """Check if the display is empty."""
        return len(self.display) == 0

    def __repr__(self) -> str:
        return (
            f"CardMarket({len(self.display)} displayed, "
            f"{len(self.stack)} in stack)"
        )
