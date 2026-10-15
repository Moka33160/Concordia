"""
File: card_manager.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Plays the cards through the action registry, and says which ones
             are playable.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from concordia.actions import ACTIONS, PLAYABILITY
from concordia.actions.context import ActionContext
from concordia.actions.drivers import Answer, run_flow

if TYPE_CHECKING:
    from concordia.actions.requests import Flow
    from concordia.models.card import Card
    from concordia.models.player import Player
    from concordia.state.game_state import GameState


class CardManager:
    """Play the cards of the game, whatever they were drawn from."""

    def __init__(self, game_state: GameState):
        """
        :param game_state: The game the played cards act upon.
        """
        self.game_state = game_state

    def context(self, card: Card, player: Player) -> ActionContext:
        """
        The context a card acts through.

        :param card: The card being played.
        :param player: The player playing it.
        :return: The card, the player and the game, in one place.
        """
        return ActionContext(card, player, self.game_state)

    def is_playable(self, card: Card, player: Player) -> bool:
        """
        Whether a card is worth playing right now.

        :param card: The card being weighed.
        :param player: The player holding it.
        :return: True when the card could act, False when it could not, and
            False for a card the game has no action for.
        """
        answers = PLAYABILITY.get(card.name)

        if answers is None:
            return False

        return answers(self.context(card, player))

    def flow(self, card: Card, player: Player) -> Flow | None:
        """
        Start a card, without driving it.

        :param card: The card being played.
        :param player: The player playing it.
        :return: The action's generator, None when the card has none.
        """
        action = ACTIONS.get(card.name)

        if action is None:
            return None

        return action(self.context(card, player))

    def lay_down(self, card: Card, player: Player) -> None:
        """
        Put a card face up in its player's pile, before it is carried out.

        :param card: The card being played.
        :param player: The player playing it.
        """
        if card in player.hand:
            player.hand.remove(card)

        if card not in player.discarded_cards:
            player.discarded_cards.append(card)

    def take_back(self, card: Card, player: Player,
                  at: int | None = None) -> None:
        """
        Undo a `lay_down`: pick the card back up off the pile.

        :param card: The card to pick back up.
        :param player: The player who laid it down.
        :param at: Where in the hand it was, so a card put back lands where it
            was picked up rather than at the end of the row.
        """
        if card in player.discarded_cards:
            player.discarded_cards.remove(card)

        if card in player.hand:
            return

        if at is None:
            player.add_to_hand(card)
            return

        player.hand.insert(min(at, len(player.hand)), card)

    def play(self, card: Card, player: Player, answer: Answer) -> bool:
        """
        Play a card from start to finish, answering it along the way.

        :param card: The card being played.
        :param player: The player playing it.
        :param answer: What answers the action's requests, an AI or a test.
        :return: True when the action was carried out, False when it found
            nothing to do. The card is played and discarded either way.
        """
        flow = self.flow(card, player)

        if flow is None:
            print(f"{card.name} has no action implemented yet.")
            return False

        self.lay_down(card, player)

        return run_flow(flow, answer)
