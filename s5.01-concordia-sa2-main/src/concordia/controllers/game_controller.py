"""
File: game_controller.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The controller of the game: it runs the setup and holds the game
             state.
"""
import random

from concordia.actions.drivers import AiAnswerer
from concordia.config import GameConfig
from concordia.controllers.game_builder import GameBuilder
from concordia.db.database_controller import DatabaseController
from concordia.managers.card_manager import CardManager
from concordia.managers.score_manager import ScoreManager
from concordia.models.card import Card
from concordia.models.player import Player
from concordia.state.game_state import GameState

# A safety limit, not a rule: it stops a game that would never end.
MAX_TURNS_PER_PLAYER = 800


class GameController:
    """
    The controller for the game, running the setup then holding the game
    state.
    """

    def __init__(self, config: GameConfig, dbc: DatabaseController,
                 autorun: bool = True, rng: random.Random | None = None):
        """
        :param config: The parsed command line configuration.
        :param dbc: The controller the setup reads the ORDB through.
        :param autorun: Whether to play the game out straight away. The
            GUI builds the game without it, since a game already played
            to its end has nothing left to show.
        :param rng: The random generator the headless game picks with,
            kept injectable for tests.
        """
        self.config = config
        self.dbc = dbc
        self.rng = rng or random.Random()

        builder = GameBuilder(config, dbc)
        self.game: GameState = builder.build()
        self.cards = CardManager(self.game)

        if autorun:
            self.run()

    def run(self):
        """Run the game loop until the last turn has been played."""
        turn_nb: int = 0
        idle_turns: int = 0
        idle_limit = 2 * len(self.game.players)
        turn_limit = MAX_TURNS_PER_PLAYER * len(self.game.players)

        while self.game.is_running():
            player = self.game.next_player
            turn_nb += 1

            if turn_nb > turn_limit:
                print(f"{turn_nb}. Stopping: no end in sight after "
                      f"{turn_limit} turns.")
                self.game.is_over = True
                break

            if self.play_turn(player, turn_nb):
                idle_turns = 0
            else:
                idle_turns += 1

            if idle_turns >= idle_limit:
                print(f"{turn_nb}. Nobody can act on anything any more.")
                self.game.is_over = True
                break

            if self.game.trigger_end_if_due(player):
                print(f"{turn_nb}. Player {player.color} takes the "
                      f"CONCORDIA card. Every other player has one turn "
                      f"left.")

            self.game.close_turn(player)

        return self.report_scores()

    def report_scores(self) -> dict:
        """Tally the final scores and announce the winner."""
        scores = ScoreManager(self.game)
        standings = scores.ranking()

        for rank, (player, victory_points) in enumerate(standings, start=1):
            print(f"{rank}. {player.color}: {victory_points} VP")

        winner = scores.winner()

        if winner is not None:
            print(f"{winner.color} wins.")

        return scores.score

    def playable_cards(self, player: Player) -> list[Card]:
        """The cards of a hand that have something to act on."""
        return [
            card for card in player.hand
            if self.cards.is_playable(card, player)
        ]

    def play_turn(self, player: Player, turn_nb: int) -> bool:
        """
        Let a player play one card of their hand.

        :param player: The player whose turn it is.
        :param turn_nb: The turn number, only used to log the turn.
        :return: True when the card played did something, which says whether
            the game is still making progress. False on an empty hand as well.
        """
        choices = self.playable_cards(player) or list(player.hand)

        if not choices:
            print(f"{turn_nb}. Player {player.color} "
                  f"has no card left to play.")
            return False

        # The player chooses its own card.
        played_card = player.choose_card(choices, self.game)
        print(f"{turn_nb}. Player {player.color} "
              f"played card: {played_card.name}")

        # The card is discarded before it resolves, so the TRIBUNE and the
        # DIPLOMAT see it.
        return self.cards.play(
            played_card, player, AiAnswerer(self.game, player, self.rng)
        )
