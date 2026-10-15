"""
File: player.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: A player of the game, either a human or an AI, and their common
             supply.
"""
import random
from abc import ABC, abstractmethod

from concordia.models.card import Card
from concordia.models.city import City
from concordia.models.colonist import Colonist

# The storehouse has 12 storage spaces, and a space holds either one colonist
# or one unit of goods.
STOREHOUSE_CAPACITY = 12


class Player(ABC):
    """A player, common to the human and the AI."""

    def __init__(self, color: str):
        self.color = color
        self.houses = 0
        self.has_scoring_marker = False
        self.scoring_marker_position = 0
        self.storehouse: dict[str, int] = {}
        self.storehouse_colonists: list[Colonist] = []
        self.colonists: list[Colonist] = []
        self.hand: list[Card] = []
        self.sestertii = 0
        self.order_of_play = None
        self.has_concordia = False
        # True once the player got the intermediate scoring, which is given
        # only once.
        self.has_scored_intermediate = False
        self.has_praefectus_magnus = False
        self.praefectus_magnus: Card | None = None
        self.discarded_cards: list[Card] = []

    @abstractmethod
    def choose_card(self, hand: list[Card], game_state=None) -> Card:
        """
        Pick a card to play.

        :param hand: The cards the player can choose from.
        :param game_state: The game they would be played in, which says what
            they are worth.
        :return: The chosen card.
        """

    def init_supply(self, nb_houses: int) -> None:
        """Give the player their unbuilt houses and their scoring marker."""
        self.houses = nb_houses
        self.has_scoring_marker = True

    def fill_storehouse(self, colonists: list[Colonist],
                        goods: dict[str, int]) -> None:
        """
        Fill the storehouse with the reserve colonists and the starting goods.

        :param colonists: The colonists kept in reserve, not yet on the board.
        :param goods: How many units of each good the storehouse starts with,
            keyed by good name.
        """
        self.storehouse_colonists.extend(colonists)
        for good, quantity in goods.items():
            self.storehouse[good] = (
                    self.storehouse.get(good, 0) + quantity)

    def place_colonist(self, way: str, city: City) -> Colonist | None:
        """
        Take a colonist out of reserve and place it on a city.

        :param way: land or sea, which route the colonist can move along.
        :param city: The city the colonist starts on.
        :return: The placed colonist, None when the reserve holds none of that
            way.
        """
        if not self.remove_storehouse_colonsist(way):
            return None

        colonist = Colonist(way)
        colonist.place(city)
        self.colonists.append(colonist)
        return colonist

    def place_scoring_marker(self, position: int) -> None:
        """Put the scoring marker on the scoring track."""
        self.scoring_marker_position = position

    def add_to_hand(self, card: Card) -> None:
        """Add a card to the player's hand."""
        self.hand.append(card)

    def receive_sestertii(self, amount: int) -> None:
        """Add sestertii to the player's purse."""
        self.sestertii += amount

    def give_praefectus_magnus(self, card: Card) -> None:
        """Give the PRÆFECTVS MAGNVS marker to the player."""
        self.has_praefectus_magnus = True
        self.praefectus_magnus = card

    def take_praefectus_magnus(self) -> Card | None:
        """Take the PRÆFECTVS MAGNVS marker back off the player."""
        card = self.praefectus_magnus
        self.has_praefectus_magnus = False
        self.praefectus_magnus = None
        return card

    def set_storehouse(self, good: str, nb: int) -> None:
        """
        Set how many units of a good the storehouse holds.

        :param good: The name of the good.
        :param nb: How many units it now holds.
        """
        self.storehouse[good] = nb

    def remove_storehouse_colonsist(self, way: str) -> bool:
        """
        Remove and return whether a storehouse colonist was found on the given
        way.
        """
        for colonist in self.storehouse_colonists:
            if colonist.way == way:
                self.storehouse_colonists.remove(colonist)
                return True
        return False

    def get_goods_storehouse_capacity(self) -> int:
        """How many more goods the storehouse can still take."""
        return (
                STOREHOUSE_CAPACITY
                - len(self.storehouse_colonists)
                - sum(self.storehouse.values())
        )

    def give_good_to_player(self, incoming_good: str) -> bool:
        """Add one good to the storehouse, if it still has room for it."""
        if self.get_goods_storehouse_capacity() <= 0:
            return False

        self.storehouse[incoming_good] = (
                self.storehouse.get(incoming_good, 0) + 1
        )
        return True

    def goods_in_stock(self) -> list[str]:
        """The goods the storehouse still holds at least one unit of."""
        return [
            good for good, quantity in self.storehouse.items() if quantity > 0
        ]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.color!r})"

    def has_enough_materials(self, materials: list[str]) -> bool:
        """Check whether the player has enough materials in the storehouse."""
        required_materials: dict[str, int] = {}

        for material in materials:
            required_materials[material] = (
                    required_materials.get(material, 0) + 1
            )

        for material, quantity in required_materials.items():
            if self.storehouse.get(material, 0) < quantity:
                return False

        return True

    def pay_city_cost(self, price: int, materials: list[str]) -> bool:
        """
        Pay the construction cost of a city house.

        :param price: Amount of sestertii to pay.
        :param materials: Names of the materials required for the
            construction, one entry per unit owed.
        :return: True if the payment was successful, False otherwise.
        """
        if self.sestertii < price:
            return False

        if not self.has_enough_materials(materials):
            return False

        self.sestertii -= price

        for material in materials:
            self.storehouse[material] -= 1

        return True


class HumanPlayer(Player):
    """A player controlled by a person, through the window."""

    def choose_card(self, hand: list[Card], game_state=None) -> Card:
        """
        A human player never chooses here, the card is clicked in the hand.

        :param hand: The cards the player can choose from.
        :param game_state: Unused, a human player is asked.
        :raise NotImplementedError: Always: a human player chooses through
            views.game_view.
        """
        raise NotImplementedError(
            "a human player chooses their card in the window, not here"
        )


class AIPlayer(Player):
    """A player driven by the computer."""

    def __init__(self, color: str, rng: random.Random | None = None):
        super().__init__(color)
        self._rng = rng or random.Random()

    def choose_card(self, hand: list[Card], game_state=None) -> Card:
        """
        Pick the card of the hand worth playing most.

        :param hand: The cards the player can choose from.
        :param game_state: The game they would be played in.
        :return: The chosen card.
        """
        if game_state is None:
            return self._rng.choice(hand)

        # Imported here to avoid a circular import with the actions.
        from concordia.actions.strategy import best_card

        return best_card(hand, game_state, self, self._rng)
