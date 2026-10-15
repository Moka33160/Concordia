"""
File: game_state.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The state of the game, assembled by the GameBuilder during the
             setup.
"""
import random

from concordia.config import GameConfig
from concordia.models.board import Board
from concordia.models.colonist import Colonist
from concordia.models.description import GameDescription
from concordia.models.god import God
from concordia.models.market import CardMarket
from concordia.models.player import Player
from concordia.models.resource import Good
from concordia.models.route import Route
from concordia.rules import same_god


class GameState:
    """The state of the game: the board, the card market and the players."""

    def __init__(self, config: GameConfig):
        self.config = config
        self.board: Board | None = None
        self.market: CardMarket | None = None
        self.players: list[Player] = []
        self.start_player: Player | None = None
        self.goods_by_name: dict[str, Good] = {}
        self.gods: list[God] = []
        self.next_player: Player | None = None
        self.description: GameDescription | None = None
        self.sestertii_variant_by_rank: dict[int, int] = {}
        # The turn number over the whole table: with 3 players, turn 4 opens
        # the second round.
        self.turn = 1
        # The player who plays the last turn, set once the end is triggered.
        self.final_player: Player | None = None
        self.is_over = False
        # The intermediate scoring is a variant, off unless the game asks for
        # it.
        self.intermediate_scoring = False

    def advance_to_next_player(self) -> None:
        """Move the start player to the next player in seating order."""
        if self.next_player is None:
            raise ValueError(
                "Cannot move to next player: no start player set."
            )
        current_index = self.players.index(self.next_player)
        next_index = (current_index + 1) % len(self.players)
        self.next_player = self.players[next_index]
        self.turn += 1

    def trigger_end_if_due(self, player: Player) -> bool:
        """Award the CONCORDIA card if this player has just ended the game."""
        if self.final_player is not None:
            return False

        emptied_display = (
                self.market is not None and self.market.is_display_empty()
        )

        if not (player.houses == 0 or emptied_display):
            return False

        player.has_concordia = True
        self.final_player = self.players[self.players.index(player) - 1]

        return True

    def close_turn(self, player: Player) -> None:
        """
        End a player's turn: award the CONCORDIA card if it is due, then hand
        the table on or stop the game.
        """
        self.trigger_end_if_due(player)

        if self.final_player is not None and player is self.final_player:
            self.is_over = True
            self.next_player = None
            return

        self.advance_to_next_player()

    @property
    def round(self) -> int:
        """The number of the round, counting from one."""
        if not self.players:
            return 1
        return (self.turn - 1) // len(self.players) + 1

    def is_running(self) -> bool:
        """Whether the game is still running."""
        return self.next_player is not None

    def colonist_on(self, route: Route) -> Colonist | None:
        """The colonist standing on a route, whoever owns it."""
        for player in self.players:
            for colonist in player.colonists:
                if colonist.route is route:
                    return colonist

        return None

    def is_route_free(self, route: Route) -> bool:
        """Whether a colonist can stop on a route."""
        return self.colonist_on(route) is None

    def get_player_by_color(self, color: str) -> Player | None:
        """Get a player by their color."""
        for player in self.players:
            if player.color == color:
                return player
        return None

    def set_board(self, board: Board) -> None:
        """Attach the board built from the map."""
        self.board = board

    def set_market(self, market: CardMarket) -> None:
        """Attach the prepared card market."""
        self.market = market

    def add_player(self, player: Player) -> None:
        """Seat a player."""
        self.players.append(player)

    def set_start_player(self, rng: random.Random) -> Player:
        """Pick the start player and rank every player behind them."""
        start_index = rng.randrange(len(self.players))
        turn_order = self.players[start_index:] + self.players[:start_index]
        for rank, player in enumerate(turn_order):
            player.order_of_play = rank
        self.next_player = turn_order[0]
        self.turn = 1
        return self.next_player

    def set_description(self, description: GameDescription) -> None:
        """Attach the box description read from ccd_description."""
        self.description = description

    def set_sestertii_variant(self, by_rank: dict[int, int]) -> None:
        """Attach the sestertii of the variant setup, by order of play."""
        self.sestertii_variant_by_rank = dict(by_rank)

    def set_goods(self, goods: dict[str, Good]) -> None:
        """Attach the goods available in the game, keyed by name."""
        self.goods_by_name = goods

    def get_good(self, good_name: str) -> Good | None:
        """Get a good by its name."""
        return self.goods_by_name.get(good_name)

    def get_players(self) -> list[Player]:
        """Get the list of players in the game."""
        return self.players

    def set_gods(self, gods: list[God]) -> None:
        """Set the list of gods in the game."""
        self.gods = gods

    def get_god_by_name(self, name: str) -> God | None:
        """Get a god by its name."""
        for god in self.gods:
            if same_god(god.name, name):
                return god
        return None

    def pass_praefectus_magnus(self, current_player: Player) -> None:
        """Pass the PRÆFECTVS MAGNVS to the player sitting to the right."""
        if current_player not in self.players:
            raise ValueError("Current player is not in the game.")

        card = current_player.take_praefectus_magnus()

        if card is None:
            raise ValueError("Current player has no PRÆFECTVS MAGNVS.")

        current_index = self.players.index(current_player)
        # A negative index wraps to the end of the list, so to the player on
        # the right.
        next_player = self.players[current_index - 1]
        next_player.give_praefectus_magnus(card)

    def __repr__(self) -> str:
        return f"GameState({self.config.map!r}, {len(self.players)} players)"
