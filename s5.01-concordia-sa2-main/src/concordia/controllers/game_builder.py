"""
File: game_builder.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The builder for the game, turning the ORDB reference data into a
             GameState.
"""
import random

from concordia.config import GameConfig
from concordia.db.database_controller import DatabaseController
from concordia.models.board import Board
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.description import GameDescription
from concordia.models.god import God
from concordia.models.market import CardMarket, DisplaySlot
from concordia.models.player import AIPlayer, HumanPlayer
from concordia.models.province import Province
from concordia.models.resource import Good
from concordia.models.token import CityToken
from concordia.rules import specialist_good_for
from concordia.state.game_state import GameState

PRAEFECTUS_MAGNUS = "PRÆFECTVS MAGNVS"


class GameBuilder:
    """Build a ready-to-play GameState out of the Oracle reference data."""

    def __init__(self, config: GameConfig, dbc: DatabaseController,
                 rng: random.Random = None):
        self.config = config
        self.dbc = dbc
        self.rng = rng or random.Random()

    def build(self) -> GameState:
        """
        Run the whole setup sequence and return the resulting game state.

        :return: The built GameState, ready for the first turn.
        """
        game = GameState(self.config)
        game.set_description(self._build_description())

        gods_by_name = {
            name: God(name, significance, reward, example, victory_points)
            for name, significance, reward, example, victory_points
            in self.dbc.select_gods()
        }
        gods = list(gods_by_name.values())
        game.set_gods(gods)
        card_defs = {
            name: (gods_by_name.get(god_name), actions, example)
            for name, god_name, actions, example
            in self.dbc.select_card_definitions()
        }

        goods = self._build_goods()
        game.set_goods(goods)

        # STEP 1 - Read the ORDB and create all the objects
        board = self._build_board()
        game.set_board(board)

        # STEP 2 - distribute the city tokens
        self._distribute_city_tokens(board, goods)

        # STEP 3 - Prepare the stack of cards
        game.set_market(self._build_market(card_defs, gods_by_name, goods))

        # STEP 4 - Player setup
        self._build_players(game, board, card_defs)

        return game

    # --- Reference data ---

    def _build_description(self) -> GameDescription | None:
        """Read the box description, artists included."""
        row = self.dbc.select_description()
        if row is None:
            return None

        name, year, designer, publisher, players, age, playing_time = row
        return GameDescription(
            name=name,
            edition_year=year,
            designer=designer,
            publisher=publisher,
            players=players,
            age=age,
            playing_time=playing_time,
            artists=tuple(self.dbc.select_artists()),
        )

    def _build_goods(self) -> dict[str, Good]:
        """Read every good, with the goods a house in such a city costs."""
        build_costs: dict[str, list[str]] = {}
        for good_name, required_good in self.dbc.select_good_build_costs():
            build_costs.setdefault(good_name, []).append(required_good)

        return {
            name: Good(
                name, value, color, bonus_sestertii, build_cost_sestertii,
                build_costs.get(name, []),
            )
            for name, value, color, bonus_sestertii, build_cost_sestertii
            in self.dbc.select_goods()
        }

    # --- STEP 1 : board ---

    def _build_board(self) -> Board:
        """
        Create the board of the configured map: capital, provinces, cities and
        routes.

        :return: The board, still without its city tokens.
        """
        board = Board(self.config.map)
        board.set_way_colors(dict(self.dbc.select_ways()))
        max_x, max_y = self.dbc.select_map_bounds(self.config.map)
        board.set_bounds(max_x, max_y)

        capital_name, capital_letter, capital_x, capital_y = (
            self.dbc.select_capital(self.config.map)
        )
        board.set_capital(
            City(capital_name, capital_letter, 0, capital_x,
                 capital_y)
        )

        provinces = self.dbc.select_provinces(self.config.map)
        for province_name, roman_num, x, y in provinces:
            province = Province(province_name, roman_num, x, y)
            cities = self.dbc.select_cities(self.config.map, province_name)
            for city_name, letter, city_x, city_y in cities:
                city = City(
                    city_name, letter, self.config.nb_players, city_x, city_y
                )
                province.add_city(city)
                board.index_city(city)
            board.add_province(province)

        for city_a, city_b, kind in self.dbc.select_routes(self.config.map):
            board.add_route(city_a, city_b, kind)

        for name, color in self.dbc.select_ways():
            board.add_way(name, color)

        return board

    # --- STEP 2 : city tokens and bonus markers ---

    def _distribute_city_tokens(
            self, board: Board, goods: dict[str, Good]
    ) -> None:
        """
        Deal a token to every city of the board, then set the bonus markers.

        :param board: The board built in step 1.
        """
        tokens = [
            CityToken(roman_char, goods[good_name])
            for roman_char, good_name, n_copies
            in self.dbc.select_city_tokens()
            for _ in range(n_copies)
        ]

        board.distribute_city_tokens(tokens, self.rng)
        board.assign_bonus_markers()

    # --- STEP 3 : card market ---

    def _build_market(
            self, card_defs: dict, gods_by_name: dict[str, God],
            goods: dict[str, Good]
    ) -> CardMarket:
        """
        Fill the card market and prepare its stack for the configured player
        count.

        :param card_defs: The card definitions, keyed by name, for the
            CONCORDIA card.
        :param gods_by_name: Every god of the game, keyed by name, to resolve
            the god of each copy (DIPLOMAT-style cards vary it from copy to
            copy).
        :param goods: Every good of the game, keyed by name, to resolve the
            good each copy is themed after and its purchase cost.
        :return: The prepared market, with its display already dealt.
        """
        market = CardMarket(self._build_display_slots())

        costs: dict[str, list[Good]] = {}
        for name, good_name in self.dbc.select_card_costs():
            good = goods.get(good_name)
            if good is not None:
                costs.setdefault(name, []).append(good)

        cards = self.dbc.select_personality_cards()
        for name, god_name, deck_number, actions, good_name, example in cards:
            market.add_card(
                Card(
                    name, gods_by_name.get(god_name), actions,
                    CardOrigin.MARKET, deck_number,
                    self._good_of(name, good_name, goods),
                    self._cost_of(name, good_name, costs, goods),
                    example,
                )
            )
        market.prepare_stack(self.config.nb_players, self.rng)

        god, actions, example = card_defs["CONCORDIA"]
        market.set_aside(
            Card("CONCORDIA", god, actions, CardOrigin.AWARD,
                 example=example)
        )
        return market

    def _build_display_slots(self) -> list[DisplaySlot]:
        """Read the layout of the display area."""
        return [
            DisplaySlot(
                position=position,
                any_good_required=(any_good_required == "Y"),
                good=good,
                n_goods=n_goods,
            )
            for position, any_good_required, good, n_goods
            in self.dbc.select_display_area()
        ]

    @staticmethod
    def _good_of(
            card_name: str, good_name: str | None, goods: dict[str, Good]
    ) -> Good | None:
        """
        The good a card copy is themed after.

        :param card_name: The card name, as the ORDB spells it.
        :param good_name: The good of the copy, None off the diplomat deck.
        :param goods: Every good of the game, keyed by name.
        :return: The good, or None when the card is themed after none.
        """
        if good_name is None:
            good_name = specialist_good_for(card_name)
        return goods.get(good_name) if good_name else None

    @staticmethod
    def _cost_of(
            card_name: str, good_name: str | None,
            costs: dict[str, list[Good]], goods: dict[str, Good]
    ) -> list[Good]:
        """
        The goods a for-sale copy is bought with.

        :param card_name: The card name, as the ORDB spells it.
        :param good_name: The good of the copy, None off the diplomat deck.
        :param costs: The prices read from card_for_sale_cost, by card name.
        :param goods: Every good of the game, keyed by name.
        :return: The goods the copy costs, one entry per unit owed.
        """
        priced = costs.get(card_name)

        if priced:
            return priced

        good = goods.get(good_name) if good_name else None

        return [good] if good is not None else []

    # --- STEP 4 : players ---

    def _build_players(
            self, game: GameState, board: Board, card_defs: dict
    ) -> None:
        """
        Seat every player, give them their starting supply and hand.

        :param game: The game states to add the players to.
        :param board: The board the starting colonists are placed on.
        :param card_defs: The card definitions, keyed by name, for the hands
            and the marker.
        """
        nb_houses = self.dbc.select_starting_houses()
        starting_colonists = self.dbc.select_starting_colonists()
        starting_goods = dict(self.dbc.select_starting_goods())
        starting_cards = self.dbc.select_starting_cards()
        starting_sestertii = self.dbc.select_starting_sestertii()
        sestertii_by_rank = {
            order_of_play: n_sestertii
            for order_of_play, n_sestertii, _variant in starting_sestertii
        }
        game.set_sestertii_variant({
            order_of_play: variant
            for order_of_play, _n_sestertii, variant in starting_sestertii
        })

        # The colour of the person is held back for their seat. Under
        # --auto there is none, so the whole pool stays open to the AI.
        ai_colors = [
            color for color in self.config.player_colors
            if color != self.config.color
        ]
        self.rng.shuffle(ai_colors)

        for seat in range(self.config.nb_players):
            # Under --auto the person sits nowhere, so no seat ever matches
            # and the AI takes the whole table.
            if seat == self.config.human_position:
                player = HumanPlayer(self.config.color)
            else:
                player = AIPlayer(ai_colors.pop(), self.rng)

            player.init_supply(nb_houses)

            # The colonists placed in the capital come out of the ones the
            # player owns.
            reserve = [
                Colonist(way)
                for way, n_colonists, cap in starting_colonists
                for _ in range(n_colonists - cap)
            ]
            player.fill_storehouse(reserve, dict(starting_goods))

            for way, _n_colonists, cap in starting_colonists:
                for _ in range(cap):
                    player.place_colonist(way, board.capital)
            player.place_scoring_marker(0)

            for card_name, n_copies in starting_cards:
                god, actions, example = card_defs[card_name]
                for _ in range(n_copies):
                    player.add_to_hand(
                        Card(card_name, god, actions,
                             CardOrigin.STARTING, example=example)
                    )

            game.add_player(player)

        game.set_start_player(self.rng)
        for player in game.players:
            player.receive_sestertii(
                sestertii_by_rank[player.order_of_play + 1]
            )

        # The Praefectus Magnus goes to the last player of the order, so the
        # one sitting to the right of the start player.
        last_player = max(game.players, key=lambda seat: seat.order_of_play)

        god, actions, example = card_defs[PRAEFECTUS_MAGNUS]
        last_player.give_praefectus_magnus(
            Card(PRAEFECTUS_MAGNUS, god, actions, CardOrigin.AWARD,
                 example=example)
        )
