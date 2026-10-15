"""
File: score_manager.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Manager for handling score-related operations in the Concordia
             system.
"""
import math

from concordia.rules import (canonical_god, minerva_vp_for,
                             specialist_good_for)
from concordia.state.game_state import GameState


class ScoreManager:
    """
    Manager for handling score-related operations in the Concordia system.
    """

    def __init__(self, game_state: GameState):
        """Initialize the ScoreManager with the current game state."""
        self.game_state = game_state
        self.score = {}

    def calculate_final_scores(self):
        """
        Calculate final victory points for all players by applying god
        multipliers to all cards owned (in hand and discard pile), plus the
        Concordia card bonus.
        """
        self.score.clear()

        for player in self.game_state.players:
            self.score[player.color] = self.calculate_player_score(player)
            player.scoring_marker_position = self.score[player.color]

        return self.score

    def calculate_player_score(self, player) -> int:
        """
        Tally one player's victory points over every card they own.

        :param player: The player being scored.
        :return: Their victory points, the CONCORDIA card included.
        """
        color = player.color

        base_by_god = {
            "vesta": self.calculate_vesta(color),
            "jupiter": self.calculate_jupiter(color),
            "saturnus": self.calculate_saturnus(color),
            "mercurius": self.calculate_mercurius(color),
            "mars": self.calculate_mars(color),
        }

        total_player_vp = 0

        for card in list(player.hand) + list(player.discarded_cards):
            god = card.god

            if god is None:
                # The PRÆFECTVS MAGNVS tile carries no god, so it scores
                # nothing.
                continue

            # The ORDB spells them JVPITER, SATVRNVS, MERCVRIVS.
            god_name = canonical_god(god.name)

            if god_name in base_by_god:
                total_player_vp += base_by_god[god_name]
            elif god_name == "minerva":
                # The good comes from the database when the card has one, from
                # its name otherwise.
                good_name = (
                    card.good.name if card.good is not None
                    else specialist_good_for(card.name)
                )

                if good_name is None:
                    continue

                total_player_vp += self.calculate_minerva(
                    color, good_name, minerva_vp_for(good_name)
                )

        if player.has_concordia:
            total_player_vp += 7

        return total_player_vp

    # --- Winning ---

    def ranking(self) -> list:
        """The players in finishing order, best first."""
        scores = self.calculate_final_scores()

        return sorted(
            ((player, scores[player.color])
             for player in self.game_state.players),
            key=lambda pair: (-pair[1], self.marker_distance(pair[0])),
        )

    def marker_distance(self, player) -> int:
        """How many hands the PRÆFECTVS MAGNVS is from reaching a player."""
        players = self.game_state.players

        if not players:
            return 0

        holder = next(
            (seat for seat in players if seat.has_praefectus_magnus), None
        )

        if holder is None:
            return 0

        start = players.index(holder)

        for step in range(len(players)):
            # The tile is handed to the right, so backwards in the player list.
            if players[start - step] is player:
                return step

        return len(players)

    def winner(self):
        """The player who wins the game."""
        standings = self.ranking()

        return standings[0][0] if standings else None

    # --- Intermediate scoring ---

    def intermediate_score(self, player) -> int:
        """
        Score a player where they stand, the first time they play a TRIBUNE.
        """
        total = self.calculate_player_score(player)
        player.scoring_marker_position = total
        player.has_scored_intermediate = True

        return total

    def close_intermediate_scoring(self) -> dict:
        """
        Pay out the intermediate scoring once every player has had theirs.
        """
        players = self.game_state.players
        paid: dict[str, int] = {}

        if not all(
                getattr(seat, "has_scored_intermediate", False)
                for seat in players
        ):
            return paid

        places = sorted(
            {seat.scoring_marker_position for seat in players}, reverse=True
        )
        reward_by_place = dict(zip(places, (2, 1)))

        for seat in players:
            reward = reward_by_place.get(seat.scoring_marker_position, 0)
            seat.receive_sestertii(reward)
            seat.scoring_marker_position = 0
            paid[seat.color] = reward

        return paid

    def calculate_vesta(self, player_color: str):
        """Calculate the Vesta bonus for a given player."""
        total_sestertii = 0

        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        if self.game_state.board is None:
            return 0

        total_sestertii += player.sestertii

        # The storehouse is keyed by good name, so the value is read from the
        # game.
        for good_name, number in player.storehouse.items():
            good = self.game_state.get_good(good_name)
            if good is not None:
                total_sestertii += number * good.value

        return math.floor(total_sestertii / 10)

    def calculate_jupiter(self, player_color: str):
        """
        Calculate the Jupiter bonus for a given player.

        :param player_color: The color of the player to calculate the bonus
            for.
        :return: The Jupiter bonus points.
        """
        total_vp = 0

        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        god = self.game_state.get_god_by_name("Jupiter")
        if god:
            god_vp = god.victory_points
        else:
            god_vp = 1

        if self.game_state.board is None:
            return 0

        for city in self.game_state.board.cities():
            if city.token is None or city.token.good.name == "brick":
                continue

            houses = city.houses
            if not houses:
                continue

            for house_color in houses:
                if player.color == house_color:
                    total_vp += god_vp

        return min(total_vp, 15)

    def calculate_saturnus(self, player_color: str):
        """
        Calculate the Saturnus bonus for a given player.

        :param player_color: The color of the player to calculate the bonus
            for.
        :return: The Saturnus bonus points.
        """
        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        if self.game_state.board is None:
            return 0

        god = (self.game_state.get_god_by_name("Saturnus")
               or self.game_state.get_god_by_name("Saturn"))
        if god:
            god_vp = god.victory_points
        else:
            god_vp = 1

        provinces_with_player_houses = set()
        for province in self.game_state.board.provinces:
            for city in province.cities:
                for house_color in city.houses:
                    if house_color == player.color:
                        provinces_with_player_houses.add(province.name)
                        break
                if province.name in provinces_with_player_houses:
                    break

        # The cap is the number of provinces of the map: 11 for Italia, 12 for
        # Imperium.
        max_vp = len(self.game_state.board.provinces)

        return min(len(provinces_with_player_houses) * god_vp, max_vp)

    def calculate_mercurius(self, player_color: str):
        """
        Calculate the Mercurius bonus for a given player.

        :param player_color: The color of the player to calculate the bonus
            for.
        :return: The Mercurius bonus points.
        """
        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        if self.game_state.board is None:
            return 0

        god = (self.game_state.get_god_by_name("Mercurius")
               or self.game_state.get_god_by_name("Mercury"))
        if god:
            god_vp = god.victory_points
        else:
            god_vp = 2

        produced_goods = set()
        for city in self.game_state.board.cities():
            if city.token is None or city.token.good is None:
                continue

            houses = city.houses
            if not houses:
                continue

            for house_color in houses:
                if player.color == house_color:
                    produced_goods.add(city.token.good.name)
                    break

        return min(len(produced_goods) * god_vp, 10)

    def calculate_mars(self, player_color: str):
        """Calculate the Mars bonus for a given player."""
        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        god = self.game_state.get_god_by_name("Mars")
        if god:
            god_vp = god.victory_points
        else:
            god_vp = 2

        return min(len(player.colonists) * god_vp, 12)

    def calculate_minerva(self, player_color: str, good_name: str,
                          vp_per_city: int):
        """
        Calculate the Minerva bonus for a given player and a specific
        specialist good type.

        :param player_color: The color of the player to calculate the bonus
            for.
        :param good_name: The target good name (e.g. 'brick', 'food', 'iron',
            'wine', 'cloth').
        :param vp_per_city: The victory points rewarded per matching city.
        :return: The Minerva bonus points for this specific specialist.
        """
        player = self.game_state.get_player_by_color(player_color)
        if player is None:
            return 0

        if self.game_state.board is None:
            return 0

        matching_houses_count = 0

        for city in self.game_state.board.cities():
            if city.token is None or city.token.good is None:
                continue

            if city.token.good.name.lower() != good_name.lower():
                continue

            houses = city.houses
            if not houses:
                continue

            for house_color in houses:
                if player.color == house_color:
                    matching_houses_count += 1
                    break

        return matching_houses_count * vp_per_city
