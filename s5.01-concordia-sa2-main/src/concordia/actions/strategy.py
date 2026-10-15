"""
File: strategy.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 11-09-2026
Description: How an AI player chooses a card and answers the requests of an
             action.
"""
from __future__ import annotations

import random
from collections import Counter
from typing import TYPE_CHECKING, Any, Callable

from concordia.actions import (architect, colonist as colonist_action,
                               diplomat, senator)
from concordia.actions.context import ActionContext
from concordia.actions.requests import (
    ChooseAmount, ChooseCity, ChooseColonist, ChooseDiscardCard, ChooseGood,
    ChooseMarketCard, ChooseOption, ChooseProvince, ChooseRoute, ChooseWay,
    Confirm, Request,
)
from concordia.models.city import City
from concordia.models.route import Route
from concordia.rules import COLONIST_COST, canonical_god, minerva_vp_for

if TYPE_CHECKING:
    from concordia.models.card import Card
    from concordia.models.colonist import Colonist
    from concordia.models.player import Player
    from concordia.models.province import Province
    from concordia.state.game_state import GameState

# The weights below come from the scoring of the gods.
FIRST_IN_PROVINCE = 4.0
FIRST_OF_GOOD = 5.0
# JVPITER pays 1 point per house outside a brick city, and brick cities are the
# cheap ones.
NOT_BRICK = 2.0
# What a sestertius is worth in victory points: VESTA pays 1 per 10.
PER_SESTERTIUS = 0.1

# What a colonist on the board is worth: 2 points from MARS, plus the houses it
# allows.
COLONIST_WORTH = 6.0

# What any card is worth just by being a card: one more action.
CARD_BASE_WORTH = 2.0

# Bonus for a good a planned house is missing.
NEEDED_BONUS = 3.0

# How many types of goods one MERCATOR can trade.
MOST_TRADES = 2

# The cost of one ARCHITECT move, so a colonist does not walk across the map.
STEP_COST = 1.5

# What moving is worth against building, since the house waits for the next
# ARCHITECT.
REACH_DISCOUNT = 0.6


def value_of(game_state: GameState, good_name: str) -> int:
    """
    What a good is worth on the table.

    :param game_state: The game, which holds the goods by name.
    :param good_name: The name of the good.
    :return: Its value, 0 for a good this game does not have.
    """
    known = game_state.goods_by_name.get(good_name)

    return 0 if known is None else known.value


def city_province(game_state: GameState, city: City) -> Province | None:
    """
    The province a city belongs to.

    :param game_state: The game whose board to look in.
    :param city: The city being placed.
    :return: Its province, None for the capital.
    """
    board = game_state.board

    for province in ([] if board is None else board.provinces):
        if city in province.cities:
            return province

    return None


class Strategy:
    """What an AI player wants, one request at a time."""

    def __init__(self, game_state: GameState, player: Player,
                 rng: random.Random | None = None):
        """
        :param game_state: The game being played.
        :param player: The seat being answered for.
        :param rng: The random generator, kept injectable for tests and
            used only to break ties.
        """
        self.game_state = game_state
        self.player = player
        self._rng = rng or random.Random()
        self._wanted: Counter | None = None
        # The caches, with the counters saying when they are out of date.
        self._province_of: dict | None = None
        self._produced: set[str] | None = None
        self._produced_stamp: int | None = None
        self._build: dict = {}
        self._blocked: dict | None = None
        # The last option and the last good chosen: the MERCATOR needs them.
        self._branch: str = ""
        self._good_chosen: str = ""

    # --- Answering ---

    def __call__(self, request: Request) -> Any:
        """
        Answer one request with the option worth the most.

        :param request: What the action is waiting on.
        :return: One of the options, or None to decline an optional offer that
            is worth less than nothing.
        """
        if isinstance(request, Confirm):
            return self._confirm()

        if isinstance(request, ChooseAmount):
            return self._amount(request)

        if not request.options:
            return None

        if isinstance(request, ChooseOption):
            return self._remember_branch(
                self._pick(request, self.option_worth)
            )

        if isinstance(request, ChooseGood):
            return self._remember_good(self._good(request))

        if isinstance(request, ChooseCity):
            measure = self.build_worth if request.optional else \
                self.reach_worth
            return self._pick(request, measure)

        if isinstance(request, ChooseColonist):
            return self._pick(request, self.colonist_worth)

        if isinstance(request, ChooseRoute):
            return self._pick(request, lambda route: self.route_worth(
                route, request.cost(route)
            ))

        if isinstance(request, ChooseProvince):
            return self._pick(request, self.province_worth)

        if isinstance(request, ChooseMarketCard):
            return self._pick(request, self.card_worth)

        if isinstance(request, ChooseDiscardCard):
            return self._pick(request, lambda pair: self.copy_worth(pair[1]))

        if isinstance(request, ChooseWay):
            return self._pick(request, self.way_worth)

        return self._rng.choice(request.options)

    def _pick(self, request: Request, worth: Callable[[Any], float]) -> Any:
        """
        The option worth the most, ties broken at random.

        :param request: The request being answered.
        :param worth: What one option is worth, the more the better.
        :return: The best option, or None when every one is a loss and the
            request is optional.
        """
        scored = [(worth(option), option) for option in request.options]
        best = max(score for score, _option in scored)

        if best < 0 and request.optional:
            return None

        return self._rng.choice(
            [option for score, option in scored if score == best]
        )

    def _remember_branch(self, option: Any) -> Any:
        """Note which branch of an action was taken, and hand it back."""
        self._branch = getattr(option, "key", "")

        return option

    def _remember_good(self, good: str | None) -> str | None:
        """Note which good was chosen, and hand it back."""
        self._good_chosen = good or ""

        return good

    # A game under test may have no board, so it is read through these.

    @property
    def cities(self) -> list[City]:
        """Every city of the board, empty when there is no board."""
        board = self.game_state.board

        return [] if board is None else board.cities()

    @property
    def routes(self) -> list[Route]:
        """Every route of the board, empty when there is no board."""
        board = self.game_state.board

        return [] if board is None else list(board.routes)

    @property
    def provinces(self) -> list:
        """Every province of the board, empty when there is no board."""
        board = self.game_state.board

        return [] if board is None else list(board.provinces)

    def province_of(self, city: City) -> Province | None:
        """The province a city belongs to, off an index built once."""
        if self._province_of is None:
            self._province_of = {
                held: province for province in self.provinces
                for held in province.cities
            }

        return self._province_of.get(city)

    @property
    def display(self) -> list:
        """The cards of the market display, empty when there is none."""
        market = self.game_state.market

        return [] if market is None else list(market.display)

    # --- What the player is saving for ---

    def wanted(self) -> Counter:
        """The goods some plan of the AI's is short of."""
        if self._wanted is not None:
            return self._wanted

        want: Counter = Counter()

        for city in self.reached_cities():
            good = city.good

            if good is not None:
                want.update(good.build_cost_goods)

        if self.player.storehouse_colonists:
            want.update(COLONIST_COST)

        for card in self.display:
            if card is not None:
                want.update(good.name for good in card.cost)

        self._wanted = want

        return want

    def reached_cities(self) -> list[City]:
        """Every city one of the player's colonists is standing next to."""
        reached: list[City] = []

        for colonist in self.player.colonists:
            position = colonist.position

            if isinstance(position, Route):
                touching = position.cities
            elif isinstance(position, City):
                touching = (position,)
            else:
                continue

            for city in touching:
                if city not in reached:
                    reached.append(city)

        return reached

    def produced_goods(self) -> set[str]:
        """The goods the player's houses already produce."""
        if self._produced_stamp != self.player.houses:
            self._produced = {
                city.good.name for city in self.cities
                if self.player.color in city.houses and city.good is not None
            }
            self._produced_stamp = self.player.houses

        return self._produced

    def settled_in(self, province: Province | None) -> bool:
        """Whether the player already has a house in a province."""
        if province is None:
            return False

        return any(
            self.player.color in city.houses for city in province.cities
        )

    # --- Houses ---

    def build_worth(self, city: City) -> float:
        """
        What putting a house in a city is worth.

        :param city: The city a house would go in.
        :return: What the house is worth, which goes negative for a dear city
            offering nothing the player has not already got.
        """
        good = city.good

        if good is None or city.is_full:
            return 0.0

        # A house built anywhere changes the value, so both counts are checked.
        stamp = (self.player.houses, len(city.houses))
        remembered = self._build.get(city)

        if remembered is not None and remembered[0] == stamp:
            return remembered[1]

        worth = float(minerva_vp_for(good.name))

        if not self.settled_in(self.province_of(city)):
            worth += FIRST_IN_PROVINCE

        if good.name not in self.produced_goods():
            worth += FIRST_OF_GOOD

        if good.name.lower() != "brick":
            worth += NOT_BRICK

        price = good.build_cost_sestertii * (city.get_nb_house() + 1)
        worth -= price * PER_SESTERTIUS
        self._build[city] = (stamp, worth)

        return worth

    def reach_worth(self, city: City) -> float:
        """What standing a colonist in or beside a city is worth."""
        worth = self.build_worth(city)

        for route in self.routes:
            if not route.touches(city):
                continue

            neighbour = route.other_end(city)

            if neighbour is not None:
                worth += self.build_worth(neighbour) / 2

        return worth

    # --- Pieces on the map ---

    def colonist_worth(self, colonist: Colonist) -> float:
        """
        What picking a colonist up is worth: the best thing it can reach in
        one step.
        """
        position = colonist.position

        if position is None:
            return 0.0

        return max(
            (
                self.route_worth(route, 1)
                for route in self.routes
                if self._steps_onto(position, route)
            ),
            default=0.0,
        )

    def route_worth(self, route: Route, steps: int) -> float:
        """
        What standing a colonist on a route is worth, less what it costs.

        :param route: The route on offer.
        :param steps: What reaching it spends.
        :return: What the move is worth.
        """
        best = max(
            (self.build_worth(city) for city in route.cities), default=0.0
        )

        return best - (steps - 1) * STEP_COST

    @staticmethod
    def _steps_onto(position, route: Route) -> bool:
        """
        Whether a colonist standing somewhere could step onto a route.

        :param position: Where the colonist stands, a city or a route.
        :param route: The route being weighed.
        :return: True when the two meet.
        """
        if isinstance(position, Route):
            return position.is_adjacent(route)

        return route.touches(position)

    def province_worth(self, province: Province) -> float:
        """What producing in a province is worth: what it would pay out."""
        worth = 0.0

        for city in province.cities:
            good = city.good

            if good is None:
                continue

            mine = sum(
                1 for color in city.houses if color == self.player.color
            )
            worth += mine * self.good_appetite(good.name)

        marker = province.bonus_marker

        if marker is not None and marker.good is not None:
            doubled = 2 if self.player.has_praefectus_magnus else 1
            worth += doubled * self.good_appetite(marker.good.name)

        return worth

    def way_worth(self, way: str) -> float:
        """What a kind of colonist is worth: how much map it opens."""
        return max(
            (
                self.route_worth(route, 1)
                for route in self.routes
                if route.kind == way
                and self.game_state.is_route_free(route)
            ),
            default=0.0,
        )

    # --- Goods ---

    def blocked_builds(self) -> dict[str, float]:
        """
        The goods standing between the player and a house, and what that house
        is worth.

        :return: What each missing good would unlock, the best house per good.
        """
        if self._blocked is not None:
            return self._blocked

        blocking: dict[str, float] = {}
        purse = self.player.sestertii

        for city in self.reached_cities():
            good = city.good

            if good is None or city.is_full:
                continue

            price = good.build_cost_sestertii * (city.get_nb_house() + 1)
            needed = Counter(good.build_cost_goods)
            missing = {
                name: short for name, short in (
                    (name, count - self.player.storehouse.get(name, 0))
                    for name, count in needed.items()
                ) if short > 0
            }

            if not missing or len(missing) > MOST_TRADES:
                continue

            bill = sum(
                value_of(self.game_state, name) * short
                for name, short in missing.items()
            )

            if purse < price + bill:
                continue

            worth = self.build_worth(city)

            for name in missing:
                blocking[name] = max(blocking.get(name, 0.0), worth)

        self._blocked = blocking

        return blocking

    def good_appetite(self, good_name: str) -> float:
        """
        How badly the player wants one more unit of a good: its value, plus a
        bonus when a planned house is missing it.
        """
        worth = float(value_of(self.game_state, good_name))
        held = self.player.storehouse.get(good_name, 0)
        short = self.wanted()[good_name] - held

        if short > 0:
            worth += NEEDED_BONUS

        return worth + self.blocked_builds().get(good_name, 0.0)

    def sale_worth(self, good_name: str) -> float:
        """What selling a unit of a good raises, against being without it."""
        raised = float(value_of(self.game_state, good_name))
        held = self.player.storehouse.get(good_name, 0)
        short = self.wanted()[good_name] - held
        owed = NEEDED_BONUS * 2 if short > 0 else 0.0

        return raised - owed - self.blocked_builds().get(good_name, 0.0)

    def _good(self, request: ChooseGood) -> str | None:
        """
        Answer a question about a good, in one of the three senses it can be
        asked.
        """
        if not request.giving_up:
            return self._pick(request, self.good_appetite)

        if request.optional:
            return self._pick(request, self.sale_worth)

        return self._pick(request, lambda good: -self.good_appetite(good))

    # --- Cards ---

    def card_worth(self, card: Card) -> float:
        """
        What buying a card off the display is worth.

        :param card: The card on offer.
        :return: What it is worth to this player.
        """
        god = canonical_god(card.god.name if card.god else None)
        worth = CARD_BASE_WORTH + sum(
            good.value for good in card.cost
        ) * PER_SESTERTIUS

        if god == "minerva":
            good_name = card.good.name if card.good else None
            cities = sum(
                1 for city in self.cities
                if self.player.color in city.houses
                and city.good is not None
                and good_name is not None
                and city.good.name == good_name
            )
            # Half for the cities not settled yet: a specialist is bought for
            # later.
            return worth + minerva_vp_for(good_name) * (cities + 0.5)

        if god == "vesta":
            return worth + 1.0

        if god in ("jupiter", "saturnus"):
            return worth + len(self.produced_goods()) + 1.0

        if god == "mercurius":
            return worth + 2.0 * len(self.produced_goods())

        if god == "mars":
            return worth + 2.0 * len(self.player.colonists)

        return worth

    def copy_worth(self, card: Card) -> float:
        """What copying a card off an opponent's pile is worth."""
        return evaluate(card, self.context(card))

    def context(self, card: Card) -> ActionContext:
        """The context a card would act through for this player."""
        return ActionContext(card, self.player, self.game_state)

    # --- Branches, amounts and confirmations ---

    def option_worth(self, option) -> float:
        """
        What one branch of an action is worth.

        :param option: The branch on offer.
        :return: What taking it is worth.
        """
        key = getattr(option, "key", "")

        if key == "place":
            return COLONIST_WORTH

        if key == "sestertii":
            # This branch is alone only when no colonist could be placed.
            return 1.0

        if key == "produce":
            return max(
                (
                    self.province_worth(province)
                    for province in self.provinces
                    if not province.is_flipped
                ),
                default=0.0,
            )

        if key == "collect":
            flipped = sum(
                1 for province in self.provinces if province.is_flipped
            )
            return flipped * 5 * PER_SESTERTIUS

        if key == "buy":
            # Only worth it for a good a planned house is missing.
            return max(
                (
                    self.good_appetite(name) - value_of(self.game_state,
                                                        name)
                    for name in self.game_state.goods_by_name
                ),
                default=0.0,
            )

        if key == "sell":
            # Only sell when the purse cannot pay for what the player wants.
            return 3.0 if self.player.sestertii < 10 else 0.5

        return 1.0

    def _amount(self, request: ChooseAmount) -> int:
        """How many units to trade."""
        if self._branch != "buy" or not self._good_chosen:
            return request.maximum

        held = self.player.storehouse.get(self._good_chosen, 0)
        short = self.wanted()[self._good_chosen] - held
        within = min(request.maximum, max(request.minimum, short))

        return max(request.minimum, within)

    def _confirm(self) -> bool:
        """Answer the one yes-or-no the game asks: the TRIBUNE's colonist."""
        return True


# --- What a card in hand is worth playing ---

def evaluate(card: Card, ctx: ActionContext) -> float:
    """
    What playing a card right now is worth.

    :param card: The card being weighed.
    :param ctx: The card, the player and the game it would act in.
    :return: What playing it is worth, never negative since passing is not
        allowed.
    """
    scorer = EVALUATORS.get(card.name)
    worth = 0.0 if scorer is None else scorer(ctx)

    return max(0.0, worth)


def _plan(ctx: ActionContext) -> Strategy:
    """A strategy for the player who would play the card."""
    return Strategy(ctx.game_state, ctx.player)


def _architect_worth(ctx: ActionContext) -> float:
    """
    What the ARCHITECT is worth: the houses it can put up right now, plus a
    little for the walking that sets up the next ones.
    """
    plan = _plan(ctx)
    worth = sum(
        max(0.0, plan.build_worth(city))
        for city in architect.buildable_cities(ctx)
    )

    if architect.any_step(ctx):
        reach = max(
            (
                plan.colonist_worth(colonist)
                for colonist in architect.movable_colonists(ctx)
            ),
            default=0.0,
        )
        worth += max(0.0, reach) * REACH_DISCOUNT

    return worth


def _colonist_worth(ctx: ActionContext) -> float:
    """What the COLONIST is worth: a colonist placed, or the sestertii."""
    if colonist_action.can_place(ctx):
        return COLONIST_WORTH

    return 2.0


def _prefect_worth(ctx: ActionContext) -> float:
    """
    What the PREFECT is worth: the best province it could produce in, or what
    the turned markers would pay.
    """
    plan = _plan(ctx)
    board = ctx.game_state.board
    produce = max(
        (
            plan.province_worth(province) for province in board.provinces
            if not province.is_flipped
        ),
        default=0.0,
    )
    collect = sum(
        1 for province in board.provinces if province.is_flipped
    ) * 5 * PER_SESTERTIUS

    return max(produce, collect)


def _senator_worth(ctx: ActionContext) -> float:
    """What the SENATOR is worth: the two best cards it could buy."""
    return _buying_worth(ctx, senator.MAX_PURCHASES, slot_surcharge=True)


def _consul_worth(ctx: ActionContext) -> float:
    """
    What the CONSUL is worth: the best card it could buy, at the printed
    price.
    """
    return _buying_worth(ctx, 1, slot_surcharge=False)


def _buying_worth(ctx: ActionContext, most: int,
                  slot_surcharge: bool) -> float:
    """
    What the best cards within reach of the display are worth.

    :param ctx: The card, the player and the game.
    :param most: How many cards the card being weighed may buy.
    :param slot_surcharge: Whether the goods above the slot are paid too.
    :return: What buying them is worth.
    """
    plan = _plan(ctx)
    best = sorted(
        (
            plan.card_worth(card)
            for card in senator.affordable_cards(ctx, slot_surcharge)
        ),
        reverse=True,
    )

    return sum(best[:most])


# How few cards must be left in hand before the TRIBUNE is the best card.
HAND_RUNNING_OUT = 3


def _tribune_worth(ctx: ActionContext) -> float:
    """
    What the TRIBUNE is worth: a hand to play out of, when there is none left.
    """
    in_hand = len(ctx.player.hand)
    pile = len(ctx.player.discarded_cards)

    if in_hand > HAND_RUNNING_OUT:
        return 1.0

    return pile * 1.5


def _specialist_worth(ctx: ActionContext) -> float:
    """
    What a MINERVA specialist is worth: one unit of its good per city of that
    good the player lives in, capped by the room to store it.
    """
    good = ctx.card.good

    if good is None:
        return 0.0

    units = sum(
        1 for city in ctx.game_state.board.cities()
        if ctx.player.color in city.houses
        and city.good is not None and city.good.name == good.name
    )
    room = ctx.player.get_goods_storehouse_capacity()

    return min(units, room) * _plan(ctx).good_appetite(good.name)


def _mercator_worth(ctx: ActionContext) -> float:
    """
    What the MERCATOR is worth: the sestertii it always pays, and the house
    its two trades would unblock.
    """
    plan = _plan(ctx)
    unlocks = max(plan.blocked_builds().values(), default=0.0)

    return 3.0 + unlocks


def _diplomat_worth(ctx: ActionContext) -> float:
    """What the DIPLOMAT is worth: the best card it could copy."""
    best = max(
        (
            evaluate(card, ctx.for_card(card))
            for _owner, card in diplomat.copyable_cards(ctx)
        ),
        default=0.0,
    )

    return best * 0.9


EVALUATORS: dict[str, Callable[[ActionContext], float]] = {
    "ARCHITECT": _architect_worth,
    "COLONIST": _colonist_worth,
    "CONSUL": _consul_worth,
    "DIPLOMAT": _diplomat_worth,
    "MERCATOR": _mercator_worth,
    "PREFECT": _prefect_worth,
    "SENATOR": _senator_worth,
    "TRIBUNE": _tribune_worth,
    "MASON": _specialist_worth,
    "FARMER": _specialist_worth,
    "WEAVER": _specialist_worth,
    "SMITH": _specialist_worth,
    "VINTNER": _specialist_worth,
}


def best_card(hand: list[Card], game_state: GameState, player: Player,
              rng: random.Random | None = None) -> Card:
    """
    The card of a hand worth playing most.

    :param hand: The cards to choose between.
    :param game_state: The game they would be played in.
    :param player: The player holding them.
    :param rng: The random generator, used only to break ties.
    :return: The chosen card.
    :raise ValueError: When the hand is empty.
    """
    if not hand:
        raise ValueError("an empty hand has no card to choose")

    rng = rng or random.Random()
    scored = [
        (evaluate(card, ActionContext(card, player, game_state)), card)
        for card in hand
    ]
    best = max(worth for worth, _card in scored)

    return rng.choice([card for worth, card in scored if worth == best])
