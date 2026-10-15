"""
File: database_controller.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Controller exposing the Concordia tables as plain Python rows.
"""
from typing import Any

from concordia.db.database_service import DatabaseService

Row = tuple[Any, ...]


class DatabaseController:
    """Read the Concordia tables through a database service."""

    def __init__(self, service: DatabaseService) -> None:
        self._service = service

    # --- Origin ---

    def get_concordia_ccd(self) -> list[Row]:
        """Return every row of the T_Concordia_CCD table."""
        self._service.connect()
        return self._service.fetch_all("SELECT * FROM T_CONCORDIA_CCD")

    # --- Description ---

    def select_description(self) -> Row | None:
        """Get the box description of the game."""
        self._service.connect()
        return self._service.fetch_one(
            "SELECT c.ccd_name, "
            "       c.ccd_description.edition_year, "
            "       c.ccd_description.designer, "
            "       c.ccd_description.publisher, "
            "       c.ccd_description.players, "
            "       c.ccd_description.age, "
            "       c.ccd_description.playing_time "
            "FROM T_CONCORDIA_CCD c"
        )

    def select_artists(self) -> list[str]:
        """Get the artists credited on the box."""
        self._service.connect()
        rows = self._service.fetch_all(
            "SELECT a.COLUMN_VALUE AS artist "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_description.artists) a"
        )
        return [artist for (artist,) in rows]

    # --- Config ---

    def get_map_player_limits(self) -> dict[str, tuple[int, int]]:
        """Return the player range of every map, keyed by map name."""
        self._service.connect()
        rows = self._service.fetch_all(
            "SELECT m.map_name, m.map_min_n_players, m.map_max_n_players "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_map) m"
        )
        return {name: (minimum, maximum) for name, minimum, maximum in rows}

    def get_player_colors(self) -> list[Row]:
        """Return the player color of every player."""
        self._service.connect()
        rows = self._service.fetch_all(
            "SELECT col.COLUMN_VALUE AS color "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_color_player) col"
        )
        return [color for (color,) in rows]

    # --- Setup: board ---

    def select_provinces(self, map_name: str) -> list[Row]:
        """Get all the provinces for a given map."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT p.province_name, p.province_roman_num, "
            "       p.province_coordinates.x, p.province_coordinates.y "
            "FROM T_CONCORDIA_CCD c, "
            "     TABLE(c.ccd_map) m, "
            "     TABLE(m.map_province) p, "
            "     TABLE(c.ccd_numeral) n "
            "WHERE m.map_name = :map_name "
            "  AND n.numeral_roman = p.province_roman_num "
            "ORDER BY n.numeral_arabic",
            {"map_name": map_name},
        )

    def select_capital(self, map_name: str) -> Row | None:
        """Get the capital of a given map."""
        self._service.connect()
        return self._service.fetch_one(
            "SELECT m.map_capital.city_name, "
            "       m.map_capital.city_roman_char, "
            "       m.map_capital.city_coordinates.x, "
            "       m.map_capital.city_coordinates.y "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_map) m "
            "WHERE m.map_name = :map_name",
            {"map_name": map_name},
        )

    def select_cities(self, map_name: str, province_name: str) -> list[Row]:
        """
        Get all the cities of a province.

        :param map_name: The name of the map the province belongs to.
        :param province_name: The name of the province to get the cities for.
        :return: A list of rows (name, roman_char, x, y).
        """
        self._service.connect()
        return self._service.fetch_all(
            "SELECT ci.city_name, ci.city_roman_char, "
            "       ci.city_coordinates.x, ci.city_coordinates.y "
            "FROM T_CONCORDIA_CCD c, "
            "     TABLE(c.ccd_map) m, "
            "     TABLE(m.map_province) p, "
            "     TABLE(p.province_city) ci "
            "WHERE m.map_name = :map_name "
            "  AND p.province_name = :province_name "
            "ORDER BY ci.city_name",
            {"map_name": map_name, "province_name": province_name},
        )

    def select_routes(self, map_name: str) -> list[Row]:
        """Get every route of a map."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT l.line_city_1, l.line_city_2, l.line_way "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_map) m, TABLE(m.map_line) l "
            "WHERE m.map_name = :map_name",
            {"map_name": map_name},
        )

    def select_ways(self) -> list[Row]:
        """Get every way a route can be, with the colour it is drawn in."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT w.way_name, w.way_color "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_way) w"
        )

    def select_map_bounds(self, map_name: str) -> Row | None:
        """Get the coordinate system's maximum extent for a map."""
        self._service.connect()
        return self._service.fetch_one(
            "SELECT m.map_max_coordinates.x, m.map_max_coordinates.y "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_map) m "
            "WHERE m.map_name = :map_name",
            {"map_name": map_name},
        )

    # --- Setup: city tokens ---

    def select_city_tokens(self) -> list[Row]:
        """Get every city token of the game."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT t.city_token_roman_char, t.city_token_good, "
            "       t.city_token_n_copies "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_city_token) t "
            "ORDER BY t.city_token_roman_char"
        )

    def select_goods(self) -> list[Row]:
        """Get every good of the game."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT g.good_name, g.good_value, g.good_color, "
            "       g.good_n_sestertii_bonus_marker, "
            "       g.good_n_sestertii_build_cost "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_good) g"
        )

    def select_good_build_costs(self) -> list[Row]:
        """Get the goods a house costs, per good produced by the city."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT g.good_name, b.COLUMN_VALUE AS required_good "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_good) g, "
            "     TABLE(g.good_build_cost) b"
        )

    def select_display_area(self) -> list[Row]:
        """Get the layout of the market display."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT d.display_area_position, "
            "       d.display_area_any_good_required, "
            "       d.display_area_good, d.display_area_n_goods "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_display_area) d "
            "ORDER BY d.display_area_position"
        )

    # --- Setup: cards ---

    def select_card_definitions(self) -> list[Row]:
        """Get every personality card of the game, deck-independent."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT cd.card_name, cd.card_god, cd.card_action, "
            "       cd.card_example "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_card) cd"
        )

    def select_personality_cards(self) -> list[Row]:
        """Get every card of the sale decks, ready to fill the card market."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT deck.card_name, deck.card_god, n.numeral_arabic, "
            "       deck.card_action, deck.card_good, deck.card_example "
            "FROM ( "
            "    SELECT cd.card_name, cd.card_god, "
            "           d.COLUMN_VALUE AS card_deck, cd.card_action, "
            "           CAST(NULL AS VARCHAR2(30)) AS card_good, "
            "           cd.card_example "
            "    FROM T_CONCORDIA_CCD c, TABLE(c.ccd_card) cd, "
            "         TABLE(cd.card_for_sale_deck) d "
            "    UNION ALL "
            "    SELECT cd.card_name, dd.card_for_sale_deck_dip_god, "
            "           dd.card_for_sale_deck_dip_deck, cd.card_action, "
            "           dd.card_for_sale_deck_dip_good, cd.card_example "
            "    FROM T_CONCORDIA_CCD c, TABLE(c.ccd_card) cd, "
            "         TABLE(cd.card_for_sale_deck_diplomat) dd "
            ") deck, T_CONCORDIA_CCD c2, TABLE(c2.ccd_numeral) n "
            "WHERE n.numeral_roman = deck.card_deck "
            "ORDER BY n.numeral_arabic, deck.card_name"
        )

    def select_card_costs(self) -> list[Row]:
        """Get the purchase price of every for-sale card."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT cd.card_name, g.COLUMN_VALUE AS good_name "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_card) cd, "
            "     TABLE(cd.card_for_sale_cost) g"
        )

    # --- Setup: player ---

    def select_starting_houses(self) -> int:
        """Get how many houses a player starts with."""
        self._service.connect()
        row = self._service.fetch_one(
            "SELECT c.ccd_setup_player.setup_p_n_houses FROM T_CONCORDIA_CCD c"
        )
        return row[0]

    def select_starting_colonists(self) -> list[Row]:
        """Get how many colonists of each way a player starts with."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT s.setup_p_colon_way, s.setup_p_colon_n_colonists, "
            "       s.setup_p_colon_n_colonists_cap "
            "FROM T_CONCORDIA_CCD c, "
            "     TABLE(c.ccd_setup_player.setup_p_colonist) s"
        )

    def select_starting_goods(self) -> list[Row]:
        """Get how many units of each good a player starts with."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT s.setup_p_good_good, s.setup_p_good_n_goods "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_setup_player.setup_p_good) s"
        )

    def select_starting_cards(self) -> list[Row]:
        """Get the personality cards a player starts with in hand."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT s.setup_p_card_card, s.setup_p_card_n_copies "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_setup_player.setup_p_card) s"
        )

    def select_starting_sestertii(self) -> list[Row]:
        """Get how many sestertii a player starts with, by order of play."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT s.setup_p_se_order_of_play, s.setup_p_se_n_sestertii, "
            "       s.setup_p_se_n_sestertii_variant "
            "FROM T_CONCORDIA_CCD c, "
            "     TABLE(c.ccd_setup_player.setup_p_sestertius) s "
            "ORDER BY s.setup_p_se_order_of_play"
        )

    # --- Scoring ---

    def select_gods(self) -> list[Row]:
        """Get every god of the game."""
        self._service.connect()
        return self._service.fetch_all(
            "SELECT g.god_name, g.god_significance, g.god_reward, "
            "g.god_example, g.god_victory_points "
            "FROM T_CONCORDIA_CCD c, TABLE(c.ccd_god) g"
        )

    # --- Helpers ---

    def close(self) -> None:
        """Release the underlying connection."""
        self._service.close()

    def __enter__(self) -> "DatabaseController":
        return self

    def __exit__(self, exception_type, exception, traceback) -> None:
        self.close()
