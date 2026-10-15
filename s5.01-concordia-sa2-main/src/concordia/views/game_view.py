"""
File: game_view.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: The Tkinter window of the game: the market, the map, the question
             asked and the hand.
"""
import tkinter as tk
from typing import Iterable

from concordia.actions.drivers import AiAnswerer
from concordia.managers.card_manager import CardManager
from concordia.managers.score_manager import ScoreManager
from concordia.models.card import Card
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.player import HumanPlayer, Player
from concordia.models.province import Province
from concordia.models.resource import Good
from concordia.models.route import Route
from concordia.state.game_state import GameState
from concordia.views import effects, highlight, province_art
from concordia.views.animation import FRAME_MS, ease_out_cubic
from concordia.views.board_art import board_photo
from concordia.views.card_art import card_photo
from concordia.views.card_detail import CardDetail
from concordia.views.card_render import draw_card_face, draw_rounded_rect
from concordia.views.choice_bar import (
    CANCEL_LABEL, GIVE_UP_LABEL, ChoiceBar,
)
from concordia.views.end_screen import (
    EndScreen, credits_lines, screen_title, standings_rows,
)
from concordia.views.good_art import good_photo
from concordia.views.hand_bar import HandBar
from concordia.views.layout import Layout
from concordia.views.market_panel import MarketPanel
from concordia.views.palette import (
    ACCENT, ACCENT_INK, BACKGROUND, CAPITAL_COLOR, CARD_BORDER, CARD_FACE,
    CARD_HEIGHT, CARD_INK, CARD_WIDTH, HIGHLIGHT, HIGHLIGHT_WIDTH,
    MAP_ACCENT, MAP_BACKGROUND, MAP_INK, MAP_MUTE, MUTED_COLOR,
    PANEL_BACKGROUND, PANEL_EDGE, PANEL_RAISED, PROVINCE_WASH,
    ROUTE_CASING, SIZE_BODY,
    SIZE_MICRO, SIZE_SMALL, SPACE_1, SPACE_2, SPACE_3, SPACE_4,
    STATUS_BACKGROUND, TEXT_COLOR, blend, ink_on, lettered, muted, sans,
    serif,
)
from concordia.views.piece_art import HOUSE, colonist_kind, piece_photo
from concordia.views.play_flow import PlayFlow
from concordia.views.played_card import PlayedCard
from concordia.views.route_layout import (
    distance_to, midpoint, route_curves,
)
from concordia.views.seat_rail import SeatRail

MAP_PADDING = 44
DEFAULT_WAY_COLOR = "#7a7166"
HUD_HEIGHT = 48

# One good of the storehouse, and the token printed on it.
CHIP_SIZE = 26
CHIP_TOKEN = 18

# The PRÆFECTVS MAGNVS tile, pinned in the band beside whoever holds it.
MARKER_WIDTH = 52
MARKER_HEIGHT = 38
MARKER_RADIUS = 4

BOARD_RADIUS = 12
MAP_TAG = "map"
GLOW_TAG = "glow"
OFFER_TAG = "offer"
CITY_RADIUS = 10
CAPITAL_RADIUS = 15

# How far a province area reaches past its cities, from the edge of a city
# disc.
PROVINCE_MARGIN = 16

# The longest gap, in map coordinates, between two cities still drawn on one
# area.
PROVINCE_LINK = 160

# The parchment ring around a city, so it stands out of the routes under it.
CITY_MOAT = 3

# The pieces on the map: the houses above a city, the colonists below it, and
# the ones walking in the middle of their route.
HOUSE_SIZE = 12
HOUSE_GAP = 2
COLONIST_WIDTH = 14
COLONIST_HEIGHT = 16
COLONIST_GAP = 2

# What a piece falls back to when there is no picture for it.
COLONIST_RADIUS = 5

# The good a city produces, printed inside the city itself.
CITY_TOKEN = 1.5
CITY_DISC_WASH = 0.55
MARKER_TOKEN = 1.3

# How near a route a click has to land to count as landing on it.
ROUTE_GRAB = 8
ROUTE_GLOW_WIDTH = 7
ROUTE_WIDTH = 3

# How often a lit route is sampled, to tell the panel where it cannot sit.
ROUTE_SAMPLE = 4

# What the casing under a route adds to its width, half of it either side.
ROUTE_CASING_MARGIN = 4

# The stroke a sea route is drawn with.
SEA_DASH = (7, 5)
SEA_KIND = "sea"

# The badge giving the cost of a route behind an occupied one.
STEP_BADGE_RADIUS = 9
# How far off the route the badge stands, so it does not land on the colonists.
STEP_BADGE_OFFSET = 13
PIECE_MARGIN = 5
GLOW_MARGIN = 5

# How far the parchment ring around a piece of lettering reaches.
HALO_RADIUS = 2
HALO_OFFSETS = tuple(
    (dx * HALO_RADIUS, dy * HALO_RADIUS)
    for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy
)

# How long an AI player waits before each answer, so the turn can be followed.
AI_SPEEDS = (("Slow", 1800), ("Normal", 900), ("Fast", 0))
DEFAULT_SPEED = 2

# The pause between two turns, so they are told apart.
BETWEEN_TURNS_MS = 320

# How long one effect takes on the map, in frames.
ANIM_FRAMES = 20
ANIM_TAG = "outcome"

# How far a floating label moves, and the gap between the labels of one turn.
LABEL_RISE = 34
LABEL_STEP = 17

# How much bigger a ring gets over the course of an outcome.
RING_GROWTH = 0.9
RING_RADIUS = 15

# The scale an opponent's discarded card is offered to the DIPLOMAT at.
OFFER_SCALE = 0.7
OFFER_GAP = 16


def storehouse_shelf(goods: Iterable[Good],
                     storehouse: dict[str, int]) -> list[tuple[str, int]]:
    """
    Every good with how many units are held, a good that ran out included.

    A good the storehouse is out of keeps its place on the shelf, so a
    MERCATOR can still buy it.

    :param goods: The goods of the game, in any order.
    :param storehouse: How many units of each good the player holds.
    :return: One (name, count) per good, from brick to cloth. Without goods,
        whatever the storehouse names, by name.
    """
    names = [good.name for good in sorted(goods, key=lambda g: g.value)]

    if not names:
        names = sorted(storehouse)

    return [(name, storehouse.get(name, 0)) for name in names]


OPENING_HINT = "Hover a card to raise it, click it to see what it does."
TURN_HINT = "Your turn. Click a lit card to play it."

# What the band has no room to spell out.
MARKER_HINT = (
    "You hold the PRÆFECTVS MAGNVS: produce with the PREFECT in a "
    "province still under its bonus marker and it pays twice, then the "
    "tile passes on."
)


def window_title(config) -> str:
    """
    What the title bar of the window says.

    :param config: The configuration the game was built from.
    :return: The map and the size of the table, saying so when the AI plays
        every seat and a screenshot would otherwise not tell.
    """
    title = f"Concordia, {config.map} ({config.nb_players} players)"
    return f"{title} — auto" if config.auto else title


def player_name(player: Player, person: Player | None) -> str:
    """
    What a player is called on screen.

    :param player: The seat to name.
    :param person: The seat played by hand, None when the AI plays them all.
    :return: The name to print, told apart from the person's own seat.
    """
    # With nobody at the table by hand there is no "you" for a seat to be the
    # rival of, so a seat stands for itself, by its colour.
    if person is None:
        return player.color.capitalize()

    who = "You" if player is person else "Rival"
    return f"{who} ({player.color})"


class GameView:
    """A Tkinter window showing the game as a table seen from above."""

    def __init__(self, game: GameState, layout: Layout | None = None):
        """
        :param game: The game to show.
        :param layout: Where the bands of the table fall, measured from
            the screen the window opens on when not given.
        """
        self.game = game
        self.cards = CardManager(game)
        self.play = PlayFlow()
        # How many turns have gone by without a card carrying its action out.
        self._idle_turns = 0
        # The AI playing the current turn, and where its turn is up to.
        self._ai: AiAnswerer | None = None
        self._ai_job: str | None = None
        # The game as it was when the played card was laid down.
        self._laid_down: dict | None = None
        self._laid_from = 0
        self._speed = DEFAULT_SPEED
        # Set by the skip key and cleared on the next turn: it skips this turn
        # only.
        self._skipping = False
        self._rise = 0.0
        self._speed_buttons: list[tk.Label] = []
        self.root = tk.Tk()
        self.root.title(window_title(game.config))
        self.root.configure(bg=BACKGROUND)

        # Measured once: nothing reflows, so the sizes hold for the whole
        # window.
        self.layout = layout or Layout.for_screen(
            self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        )
        self.root.resizable(False, False)

        # The pieces grow with the table but more slowly, or they would cover
        # the 8px fan between two ways.
        self._pieces = self.layout.card_scale

        self._status = tk.StringVar(value=OPENING_HINT)
        self._scale, self._offset = self._layout_scale()
        self._points = {
            city: self._scale_point(city.x, city.y)
            for city in game.board.cities()
        }
        # Where each route is drawn, computed once and used for the lines, the
        # colonists and the clicks.
        self._curves = dict(
            route_curves(game.board.routes, self._points)
        )
        # Same for the area of each province, which never moves either.
        self._grounds = self._province_grounds()
        self._offers: list[tuple[float, float, float, float, object]] = []

        self._build_frame()
        self.played = PlayedCard(self.canvas, self.layout)
        self._detail = CardDetail(
            self.canvas, on_play=self._play, on_close=self._clear_selection
        )
        self._end = EndScreen(self.canvas)
        self.root.bind("<Escape>", lambda _e: self._escape())
        self.root.bind("<space>", lambda _e: self._skip_ai_turn())
        self.refresh()
        self._open_on_the_start_player()

    def _p(self, base: float) -> float:
        """A base piece size at the scale this table draws pieces at."""
        return base * self._pieces

    def _open_on_the_start_player(self) -> None:
        """
        Let the seats before the person play, before handing them the table.
        """
        player = self.game.next_player

        if player is None:
            self._status.set("The game is over.")
            return

        if isinstance(player, HumanPlayer):
            self._status.set(self._turn_hint())
            return

        self._status.set(
            f"{self._player_name(player)} starts. Watching the table…"
        )
        self._later(BETWEEN_TURNS_MS, self._play_ai_turn)

    def run(self) -> None:
        """Start the Tkinter event loop; blocks until the window is closed."""
        self.root.mainloop()

    # --- Frame ---

    def _build_frame(self) -> None:
        """Build the main canvas, the HUD band and the status bar."""
        main = tk.Frame(self.root, bg=BACKGROUND)
        main.pack(fill="both", expand=True, padx=SPACE_2, pady=SPACE_2)

        self.canvas = tk.Canvas(
            main, width=self.layout.table_width,
            height=self.layout.table_height, bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda _e: self.hand.clear_hover())

        self.market = MarketPanel(
            self.canvas, self.layout,
            on_select=lambda card: self._select(card, playable=False),
            good_color=self._good_color,
        )
        self.hand = HandBar(
            self.canvas, self.layout,
            on_select=lambda card: self._select(card, playable=True),
        )
        self.choices = ChoiceBar(
            self.canvas, 0, self.layout.table_width,
            self.layout.gutter_bottom,
            on_answer=self._answer, on_cancel=self._cancel,
        )
        # Every player's supply, in the margin beside the parchment.
        self.seats = SeatRail(
            self.canvas, self.layout.table_width, self._good_color,
        )
        # The question is drawn on the board, where the player is already
        # looking.
        self.choices.set_box(*self._board_rect())
        self.seats.set_board(*self._board_rect())

        self.hud = tk.Frame(main, bg=PANEL_BACKGROUND, height=HUD_HEIGHT)
        self.hud.pack(fill="x", pady=(SPACE_2, 0))
        self.hud.pack_propagate(False)

        strip = tk.Frame(self.root, bg=STATUS_BACKGROUND)
        strip.pack(fill="x", side="bottom")

        tk.Label(
            strip, textvariable=self._status, bg=STATUS_BACKGROUND,
            fg=MUTED_COLOR, anchor="w", padx=SPACE_3, pady=SPACE_1 + 2,
            font=sans(SIZE_SMALL),
        ).pack(side="left", fill="x", expand=True)

        self._build_speed(strip)

    def _build_speed(self, strip: tk.Widget) -> None:
        """The control setting how long an AI player waits at each decision."""
        tk.Label(
            strip, text="space skips", bg=STATUS_BACKGROUND, fg=MUTED_COLOR,
            font=sans(SIZE_MICRO), padx=SPACE_2,
        ).pack(side="left")

        for index, (name, _pause) in enumerate(AI_SPEEDS):
            button = tk.Label(
                strip, text=name, bg=STATUS_BACKGROUND, fg=MUTED_COLOR,
                font=sans(SIZE_MICRO, "bold"), padx=SPACE_2,
                pady=SPACE_1 + 2, cursor="hand2",
            )
            button.pack(side="left")
            button.bind("<Button-1>", lambda _e, at=index: self._set_speed(at))
            self._speed_buttons.append(button)

        self._show_speed()

    def _set_speed(self, index: int) -> None:
        """Change how long the AI is left at each of its decisions."""
        self._speed = index
        self._show_speed()

    def _show_speed(self) -> None:
        """Mark the speed now set, and unmark the others."""
        for index, button in enumerate(self._speed_buttons):
            lit = index == self._speed
            button.configure(
                fg=ACCENT_INK if lit else MUTED_COLOR,
                bg=ACCENT if lit else STATUS_BACKGROUND,
            )

    @property
    def _pause(self) -> int:
        """How long a decision is left on screen, 0 to not stop at all."""
        return AI_SPEEDS[self._speed][1]

    def _good_color(self, name: str) -> str | None:
        """Look a good's colour up by name."""
        good = self.game.get_good(name)
        return good.color if good is not None else None

    def refresh(self) -> None:
        """Redraw the whole table from the game state as it now stands."""
        request = self.play.request

        self.canvas.delete("all")
        self._offers = []

        self._draw_map(recede=highlight.dims_the_map(request))
        self._draw_glow(request)
        self._draw_discard_offer(request)
        self._draw_seats(request)

        self.market.set_market(self.game.market)
        self.market.set_highlighted(highlight.market_cards_for(request))

        self._draw_hud()
        self.choices.set_obstacles(self._lit_points(request))
        self.choices.set_watching(self.is_watching)
        self.choices.set_way_out(self._way_out())
        self.choices.show(request)

        player = self.game.next_player
        hand = player.hand if player is not None else []
        self.hand.set_cards(hand)
        self.hand.set_playable(self._playable_cards())

        # Last and above everything: refresh clears the canvas, so the played
        # card is drawn again after it.
        self.played.redraw()

    def _draw_seats(self, request) -> None:
        """Fill the rail beside the board with the supply of every player."""
        self.seats.set_seats(
            self.game.players, self.game.next_player, self._person,
            highlight.goods_for(request) if self.is_watching else (),
        )

    @property
    def is_watching(self) -> bool:
        """Whether the current question is asked to an AI player."""
        return self._ai is not None

    def _playable_cards(self) -> list[Card]:
        """The cards of the current hand that are worth playing."""
        player = self.game.next_player

        if player is None or self.play.is_running:
            return []

        return [
            card for card in player.hand
            if self.cards.is_playable(card, player)
        ]

    # --- Map ---

    def _layout_scale(self) -> tuple[float, tuple[float, float]]:
        """
        Compute the scale and offset fitting the ORDB's own coordinate bounds
        onto the map band.
        """
        board = self.game.board
        range_x = max(board.max_x, 1)
        range_y = max(board.max_y, 1)
        padding = self._p(MAP_PADDING)
        scale = min(
            (self.layout.table_width - 2 * padding) / range_x,
            (self.layout.map_band - 2 * padding) / range_y,
        )
        offset_x = (self.layout.table_width - range_x * scale) / 2
        offset_y = (self.layout.map_band - range_y * scale) / 2
        return scale, (offset_x, offset_y)

    def _scale_point(self, x: int, y: int) -> tuple[float, float]:
        """Scale one database (x, y) coordinate to its place on the canvas."""
        offset_x, offset_y = self._offset
        return (
            offset_x + x * self._scale,
            self.layout.map_top + offset_y + y * self._scale,
        )

    def _board_rect(self) -> tuple[float, float, float, float]:
        """The parchment the board is printed on."""
        board = self.game.board
        padding = self._p(MAP_PADDING)
        left, top = self._scale_point(0, 0)
        right, bottom = self._scale_point(
            max(board.max_x, 1), max(board.max_y, 1)
        )
        return left - padding, top - padding, right + padding, bottom + padding

    def _haloed_text(self, x: float, y: float, text: str, font: tuple,
                     fill: str, tag: str) -> None:
        """
        Draw a piece of lettering with a parchment ring around it.

        :param x: The x the lettering is centred on.
        :param y: The y the lettering is centred on.
        :param text: What it reads.
        :param font: The face to draw it in.
        :param fill: The ink to draw it in.
        :param tag: The tag every item is given.
        """
        for offset_x, offset_y in HALO_OFFSETS:
            self.canvas.create_text(
                x + offset_x, y + offset_y, text=text, font=font,
                fill=MAP_BACKGROUND, tags=tag,
            )
        self.canvas.create_text(
            x, y, text=text, font=font, fill=fill, tags=tag,
        )

    def _draw_map(self, recede: bool = False) -> None:
        """
        Draw the map band: the ground under each province, the routes, the
        bonus markers and the cities.
        """
        # The paper of the board already carries the province tints.
        printed = self._draw_board(recede)
        self._draw_provinces(printed, recede)
        self._draw_routes(recede)

        # The colonists on a route go over the line and under the cities.
        for route in self._curves:
            self._draw_colonists(route, recede)

        for province in self.game.board.provinces:
            self._draw_bonus_marker(province, recede)

        for city in self.game.board.cities():
            self._draw_city(city, recede)

        for city in self.game.board.cities():
            self._name_city(city, recede)

    def _draw_board(self, recede: bool = False) -> bool:
        """
        Lay the board down: its shadow, its paper and its rim.

        :param recede: Whether the map is behind a question.
        :return: Whether the paper was drawn, with the province areas in it. A
            flat board has none, so the map draws them on the canvas itself.
        """
        left, top, right, bottom = self._board_rect()

        # A shadow under the board, so it sits on the table.
        draw_rounded_rect(
            self.canvas, left + SPACE_1, top + SPACE_1, right + SPACE_1,
            bottom + SPACE_1, 12, MAP_TAG,
            fill=STATUS_BACKGROUND, outline="",
        )

        paper = board_photo(
            right - left, bottom - top, BOARD_RADIUS, recede,
            self._printed_grounds(left, top),
        )

        if paper is None:
            draw_rounded_rect(
                self.canvas, left, top, right, bottom, BOARD_RADIUS, MAP_TAG,
                fill=MAP_BACKGROUND, outline=CARD_BORDER, width=1,
            )
            return False

        self.canvas.create_image(
            (left + right) / 2, (top + bottom) / 2, image=paper, tags=MAP_TAG,
        )
        # The rim goes over the paper, on the same curve.
        draw_rounded_rect(
            self.canvas, left, top, right, bottom, BOARD_RADIUS, MAP_TAG,
            fill="", outline=CARD_BORDER, width=1,
        )
        return True

    def _province_grounds(self) -> list[tuple[int, list[tuple[float, float]]]]:
        """The region each province covers, worked out once for the window."""
        # The margin is in table pixels, the gap between two cities in map
        # coordinates.
        margin = self._p(CITY_RADIUS + PROVINCE_MARGIN)
        link = PROVINCE_LINK * self._scale

        return [
            (index, region)
            for index, province in enumerate(self.game.board.provinces)
            for region in province_art.regions(
                [self._points[city] for city in province.cities
                 if city in self._points]
                + [self._scale_point(province.x, province.y)],
                margin, link,
            )
        ]

    def _printed_grounds(self, left: float, top: float) -> tuple:
        """
        The province areas in the coordinates of the paper.

        :param left: The left edge of the board, so x zero of the paper.
        :param top: The top edge of the board, so y zero of the paper.
        :return: One (tint, points, strength) per area, hashable for the
            cache.
        """
        return tuple(
            (province_art.tint(index),
             tuple((x - left, y - top) for x, y in region),
             PROVINCE_WASH)
            for index, region in self._grounds if region
        )

    def _draw_provinces(self, printed: bool, recede: bool = False) -> None:
        """
        Draw the ground under each province, and the line around it.

        :param printed: Whether the paper landed, carrying the washes.
        :param recede: Whether the map is sitting back behind a question.
        """
        for index, region in self._grounds:
            if not region:
                continue

            flat = [axis for point in region for axis in point]

            if not printed:
                self.canvas.create_polygon(
                    *flat, fill=muted(province_art.wash(index), recede),
                    outline="", tags=MAP_TAG,
                )

            self.canvas.create_polygon(
                *flat,
                fill="",
                outline=muted(province_art.edge(index), recede),
                width=1,
                tags=MAP_TAG,
            )

    def _draw_routes(self, recede: bool = False) -> None:
        """Draw every road of the map, each on a casing of its own."""
        way_colors = self.game.board.way_colors
        core = self._p(ROUTE_WIDTH)
        casing = core + self._p(ROUTE_CASING_MARGIN)

        for route, polyline in self._curves.items():
            flat = [axis for point in polyline for axis in point]
            self.canvas.create_line(
                *flat, fill=muted(ROUTE_CASING, recede), width=casing,
                capstyle="round", joinstyle="round", tags=MAP_TAG,
            )

        for route, polyline in self._curves.items():
            color = way_colors.get(route.kind, DEFAULT_WAY_COLOR)
            flat = [axis for point in polyline for axis in point]
            self.canvas.create_line(
                *flat, fill=muted(color, recede), width=core,
                capstyle="round", joinstyle="round", tags=MAP_TAG,
                **({"dash": SEA_DASH} if route.kind == SEA_KIND else {}),
            )

    def _city_radius(self, city: City) -> float:
        """The radius a city is drawn at, the capital being the larger."""
        return self._p(
            CAPITAL_RADIUS if city is self.game.board.capital
            else CITY_RADIUS
        )

    def _draw_city(self, city: City, recede: bool = False) -> None:
        """Draw a city, the houses built in it and the colonists on it."""
        x, y = self._points[city]
        radius = self._city_radius(city)
        capital = city is self.game.board.capital
        fill = (
            CAPITAL_COLOR if capital
            else (city.good.color if city.good else "#8a8a8a")
        )
        token = None if capital or city.good is None else self._token_image(
            city.good.name, radius * CITY_TOKEN, recede
        )
        moat = radius + self._p(CITY_MOAT)

        # The ring first: parchment over the routes, so the city is drawn on
        # the map and not in it.
        self.canvas.create_oval(
            x - moat, y - moat, x + moat, y + moat,
            fill=MAP_BACKGROUND, outline="", tags=MAP_TAG,
        )
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=muted(self._disc_fill(fill, token), recede),
            outline=muted(MAP_INK, recede), width=2, tags=MAP_TAG,
        )

        if capital:
            inner = radius - self._p(4)
            self.canvas.create_oval(
                x - inner, y - inner, x + inner, y + inner,
                fill="", outline=muted(MAP_BACKGROUND, recede), width=2,
                tags=MAP_TAG,
            )

        if token is not None:
            self.canvas.create_image(x, y, image=token, tags=MAP_TAG)

        self._draw_houses(city, recede)
        self._draw_colonists(city, recede)

    @staticmethod
    def _token_image(name: str, box: float, recede: bool):
        """
        A good's printed token, sized to sit inside a disc on the map.

        :param name: The good's name, as the ORDB spells it.
        :param box: The largest the token may be drawn, on either side.
        :param recede: Whether the map is sitting back behind a question,
            which washes the token exactly as far as the disc under it.
        :return: The Tk image, None where there is no token to draw.
        """
        return good_photo(name, box, box, MAP_MUTE if recede else 0.0)

    @staticmethod
    def _disc_fill(color: str, token) -> str:
        """
        What a good's disc is filled with, under whatever is printed on it.

        :param color: The good's own colour.
        :param token: The token to be printed on it, None for none.
        :return: The colour to fill the disc with.
        """
        return color if token is None else blend(
            color, MAP_BACKGROUND, CITY_DISC_WASH
        )

    def _name_city(self, city: City, recede: bool = False) -> None:
        """
        Write a city's name under it.

        :param city: The city to name.
        :param recede: Whether the map is sitting back behind a question.
        """
        x, y = self._points[city]
        below = (
                self._city_radius(city) + self._p(PIECE_MARGIN)
                + self._p(COLONIST_HEIGHT) + SPACE_3
        )
        self._haloed_text(
            x, y + below, city.display_name, sans(SIZE_MICRO, "bold"),
            lettered(MAP_INK, recede), MAP_TAG,
        )

    @staticmethod
    def _piece_image(kind: str, width: float, height: float,
                     color: str, recede: bool):
        """
        The outline of one piece, filled with the colour of its owner.

        :param kind: The piece, `HOUSE` or a colonist's way.
        :param width: The width the piece is drawn in.
        :param height: The height it is drawn in.
        :param color: Its owner's colour.
        :param recede: Whether the map is behind a question.
        :return: The Tk image, None when there is no picture: no Pillow, or a
            way with no drawing.
        """
        return piece_photo(
            kind, width, height, muted(color, recede),
            muted(MAP_INK, recede),
        )

    def _draw_houses(self, city: City, recede: bool = False) -> None:
        """Draw the houses built in a city, in their builders' colours."""
        if not city.houses:
            return

        x, y = self._points[city]
        size = self._p(HOUSE_SIZE)
        gap = self._p(HOUSE_GAP)
        row = len(city.houses) * size + (len(city.houses) - 1) * gap
        left = x - row / 2
        top = y - self._city_radius(city) - self._p(PIECE_MARGIN) - size

        for index, color in enumerate(city.houses):
            offset = left + index * (size + gap)
            house = self._piece_image(HOUSE, size, size, color, recede)

            if house is not None:
                self.canvas.create_image(
                    offset + size / 2, top + size / 2, image=house,
                    tags=MAP_TAG,
                )
                continue

            self.canvas.create_rectangle(
                offset, top, offset + size, top + size,
                fill=muted(color, recede),
                outline=muted(MAP_INK, recede), tags=MAP_TAG,
            )

    def _piece_anchor(self, position) -> tuple[float, float]:
        """The point the pieces standing somewhere are lined up on."""
        if isinstance(position, Route):
            return midpoint(self._curves[position])

        x, y = self._points[position]
        return (
            x,
            y + self._city_radius(position) + self._p(PIECE_MARGIN)
            + self._p(COLONIST_HEIGHT) / 2,
        )

    def _colonist_spots(self,
                        position) -> list[tuple[Colonist, float, float]]:
        """Where each colonist standing on a city or a route is drawn."""
        if not position.colonists:
            return []

        x, y = self._piece_anchor(position)
        width = self._p(COLONIST_WIDTH)
        step = width + self._p(COLONIST_GAP)
        row = len(position.colonists) * step - self._p(COLONIST_GAP)
        left = x - row / 2 + width / 2

        return [
            (colonist, left + index * step, y)
            for index, colonist in enumerate(position.colonists)
        ]

    def _colonist_colors(self) -> dict[int, str]:
        """Which player each colonist on the board belongs to."""
        return {
            id(colonist): player.color
            for player in self.game.players
            for colonist in player.colonists
        }

    def _draw_colonists(self, position, recede: bool = False) -> None:
        """Draw the colonists standing on a city or a route."""
        colors = self._colonist_colors()
        width = self._p(COLONIST_WIDTH)
        height = self._p(COLONIST_HEIGHT)
        radius = self._p(COLONIST_RADIUS)

        for colonist, cx, cy in self._colonist_spots(position):
            color = colors.get(id(colonist), MUTED_COLOR)
            piece = self._piece_image(
                colonist_kind(colonist.way), width, height, color, recede
            )

            if piece is not None:
                self.canvas.create_image(cx, cy, image=piece, tags=MAP_TAG)
                continue

            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=muted(color, recede),
                outline=muted(MAP_INK, recede), tags=MAP_TAG,
            )

    def _doubles_the_bonus(self) -> bool:
        """Whether the player about to play holds the PRÆFECTVS MAGNVS."""
        player = self.game.next_player
        return player is not None and player.has_praefectus_magnus

    def _draw_bonus_marker(self, province: Province,
                           recede: bool = False) -> None:
        """Draw a province's bonus marker at its own ORDB coordinates."""
        cx, cy = self._scale_point(province.x, province.y)
        marker = province.bonus_marker
        color = marker.good.color if marker is not None else "#cccccc"
        edge = self._p(8)
        token = None if province.is_flipped or marker is None else (
            self._token_image(marker.good.name, edge * MARKER_TOKEN, recede)
        )

        # A turned marker is spent until a PREFECT collects it, so it is drawn
        # hollow.
        draw_rounded_rect(
            self.canvas, cx - edge, cy - edge, cx + edge, cy + edge, 3,
            MAP_TAG,
            fill=MAP_BACKGROUND if province.is_flipped
            else muted(self._disc_fill(color, token), recede),
            outline=muted(MAP_INK, recede), width=1,
        )

        if token is not None:
            self.canvas.create_image(cx, cy, image=token, tags=MAP_TAG)

        self._haloed_text(
            cx, cy - edge - SPACE_2, province.roman_num,
            sans(SIZE_MICRO, "bold"), lettered(MAP_INK, recede), MAP_TAG,
        )

        # The tile doubles a bonus, so every marker still face up is marked ×2.
        if token is not None and self._doubles_the_bonus():
            self._haloed_text(
                cx, cy + edge + SPACE_2, "×2",
                sans(SIZE_MICRO, "bold"), lettered(MAP_ACCENT, recede),
                MAP_TAG,
            )

    # --- Surbrillance ---

    def _draw_glow(self, request) -> None:
        """Ring whatever the running action is offering on the map."""
        if request is None:
            return

        # The routes are drawn first: a highlighted route is thick, and the
        # cities go over it.
        for route in highlight.routes_for(request):
            self._ring_route(route)

        for route, steps in highlight.route_steps(request).items():
            self._badge_route(route, steps)

        for city in highlight.cities_for(request):
            self._ring_city(city)

        for province in highlight.provinces_for(request):
            self._ring_province(province)

        for colonist in highlight.colonists_for(request):
            self._ring_colonist(colonist)

    def _ring_city(self, city: City) -> None:
        """Ring one city in gold."""
        x, y = self._points[city]
        radius = self._city_radius(city) + self._p(GLOW_MARGIN)
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline=HIGHLIGHT, width=HIGHLIGHT_WIDTH, tags=GLOW_TAG,
        )

    def _ring_province(self, province: Province) -> None:
        """Ring one province's bonus marker in gold."""
        cx, cy = self._scale_point(province.x, province.y)
        edge = self._p(8) + self._p(GLOW_MARGIN)
        self.canvas.create_rectangle(
            cx - edge, cy - edge, cx + edge, cy + edge,
            outline=HIGHLIGHT, width=HIGHLIGHT_WIDTH, tags=GLOW_TAG,
        )

    def _ring_route(self, route: Route) -> None:
        """Trace one route in gold, along the very line it was drawn on."""
        polyline = self._curves.get(route)

        if polyline is None:
            return

        self.canvas.create_line(
            *[axis for point in polyline for axis in point],
            fill=HIGHLIGHT, width=self._p(ROUTE_GLOW_WIDTH),
            capstyle="round", joinstyle="round", tags=GLOW_TAG,
        )

    def _badge_spot(self, polyline) -> tuple[float, float]:
        """Where a route's badge stands: beside the road, not on it."""
        cx, cy = midpoint(polyline)
        start, end = polyline[0], polyline[-1]
        span_x, span_y = end[0] - start[0], end[1] - start[1]
        length = (span_x ** 2 + span_y ** 2) ** 0.5

        if length == 0:
            return cx, cy

        away = self._p(STEP_BADGE_OFFSET)
        return cx - span_y / length * away, cy + span_x / length * away

    def _badge_route(self, route: Route, steps: int) -> None:
        """
        Mark what a route costs to reach, when it is more than one step.

        :param route: The route on offer.
        :param steps: What reaching it spends.
        """
        polyline = self._curves.get(route)

        if steps <= 1 or polyline is None:
            return

        cx, cy = self._badge_spot(polyline)
        radius = self._p(STEP_BADGE_RADIUS)
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=HIGHLIGHT, outline=MAP_BACKGROUND, width=2, tags=GLOW_TAG,
        )
        self.canvas.create_text(
            cx, cy, text=str(steps), font=sans(SIZE_MICRO, "bold"),
            fill=CARD_INK, tags=GLOW_TAG,
        )

    def _ring_colonist(self, colonist: Colonist) -> None:
        """Ring one colonist in gold, wherever it stands."""
        if colonist.position is None:
            return

        wide, tall = self._colonist_reach()

        for standing, cx, cy in self._colonist_spots(colonist.position):
            if standing is colonist:
                self.canvas.create_oval(
                    cx - wide, cy - tall, cx + wide, cy + tall,
                    outline=HIGHLIGHT, width=2, tags=GLOW_TAG,
                )

    def _colonist_reach(self) -> tuple[float, float]:
        """How far a colonist reaches from where it is centred."""
        return self._p(COLONIST_WIDTH) / 2, self._p(COLONIST_HEIGHT) / 2

    def _draw_discard_offer(self, request) -> None:
        """
        Deal an opponent's last played card out for the DIPLOMAT to copy.

        :param request: What the action is waiting on, None when nothing is.
        """
        offered = sorted(
            highlight.discards_for(request),
            key=lambda pair: self.game.players.index(pair[0]),
        )

        if not offered:
            return

        scale = OFFER_SCALE * self.layout.card_scale
        width = CARD_WIDTH * scale
        gap = OFFER_GAP * self.layout.card_scale
        row = len(offered) * width + (len(offered) - 1) * gap
        left = (self.layout.table_width - row) / 2
        top = (
                self.layout.map_top + self.layout.map_band / 2
                - CARD_HEIGHT * scale / 2
        )

        for index, (owner, card) in enumerate(offered):
            x = left + index * (width + gap)
            drawn_w, drawn_h = draw_card_face(
                self.canvas, card, x, top, scale=scale, tag=OFFER_TAG,
                highlighted=True,
            )
            self._haloed_text(
                x + drawn_w / 2, top - SPACE_3,
                self._player_name(owner), sans(SIZE_MICRO, "bold"),
                MAP_INK, OFFER_TAG,
            )
            self._offers.append(
                (x, top, x + drawn_w, top + drawn_h, (owner, card))
            )

    def _lit_points(self, request) -> list[tuple[float, float]]:
        """
        Where everything the running action is offering on the board sits.

        :param request: What the action is waiting on, None when nothing is.
        :return: One (x, y) per lit thing, in canvas coordinates.
        """
        if request is None:
            return []

        points = [self._points[city] for city in highlight.cities_for(request)]

        points += [
            self._scale_point(province.x, province.y)
            for province in highlight.provinces_for(request)
        ]

        for colonist in highlight.colonists_for(request):
            if colonist.position is not None:
                points += [
                    (cx, cy) for standing, cx, cy
                    in self._colonist_spots(colonist.position)
                    if standing is colonist
                ]

        # A route is long, so several points along it are given instead of its
        # middle.
        for route in highlight.routes_for(request):
            polyline = self._curves.get(route)
            if polyline:
                points += polyline[::ROUTE_SAMPLE]
                points.append(midpoint(polyline))

        # The cards offered to the DIPLOMAT are drawn in the middle of the
        # board, where the panel would go.
        points += [
            ((x0 + x1) / 2, (y0 + y1) / 2)
            for x0, y0, x1, y1, _pair in self._offers
        ]

        return points

    # --- Hit tests ---

    def _city_at(self, x: float, y: float) -> City | None:
        """
        The city under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The city, None when the pointer is over none.
        """
        for city, (cx, cy) in self._points.items():
            radius = self._city_radius(city)
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                return city
        return None

    def _province_at(self, x: float, y: float) -> Province | None:
        """
        The province whose bonus marker is under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The province, None when the pointer is over no marker.
        """
        edge = self._p(8)

        for province in self.game.board.provinces:
            cx, cy = self._scale_point(province.x, province.y)
            if abs(x - cx) <= edge and abs(y - cy) <= edge:
                return province
        return None

    def _route_at(self, x: float, y: float, among=None) -> Route | None:
        """
        The route under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :param among: The routes to look in, every route of the board when
            None. Keeping only the offered ones makes a click between two
            routes land on the right one.
        :return: The route, None when the pointer is near none.
        """
        # A city is at the end of every route leaving it, so a click is close
        # to all of them.
        if self._city_at(x, y) is not None:
            return None

        nearest, reach = None, self._p(ROUTE_GRAB)

        for route, polyline in self._curves.items():
            if among is not None and route not in among:
                continue

            gap = distance_to((x, y), polyline)
            if gap <= reach:
                nearest, reach = route, gap

        return nearest

    def _colonist_at(self, x: float, y: float) -> Colonist | None:
        """
        The colonist under the pointer, on a city or out on a route.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The colonist, None when the pointer is over none.
        """
        standing = [*self.game.board.cities(), *self._curves]
        wide, tall = self._colonist_reach()

        for position in standing:
            for colonist, cx, cy in self._colonist_spots(position):
                if abs(x - cx) <= wide and abs(y - cy) <= tall:
                    return colonist
        return None

    def _offer_at(self, x: float, y: float):
        """
        The offered discard pile under the pointer.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        :return: The (owner, card) pair, None when over none.
        """
        for x0, y0, x1, y1, pair in self._offers:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return pair
        return None

    def _show_city(self, city: City) -> None:
        """Show a city's good in the status bar."""
        if city is self.game.board.capital:
            self._status.set(f"{city.display_name}, the capital.")
            return
        good = (
            f"{city.good.name} (value {city.good.value})"
            if city.good else "no token"
        )
        self._status.set(
            f"{city.display_name} [{city.letter}], produces {good}."
        )

    # --- HUD ---

    def _player_name(self, player: Player) -> str:
        """What a player is called on screen."""
        return player_name(player, self._person)

    def _draw_hud(self) -> None:
        """
        Redraw the band under the board with the supply of the human player.
        """
        for child in self.hud.winfo_children():
            child.destroy()

        player = self._person or self.game.next_player

        if player is None:
            return

        tk.Frame(self.hud, bg=PANEL_EDGE, height=1).pack(
            fill="x", side="top"
        )

        tk.Label(
            self.hud,
            text=f"Turn {self.game.turn}  ·  round {self.game.round}",
            fg=MUTED_COLOR, bg=PANEL_BACKGROUND, font=sans(SIZE_MICRO),
        ).pack(side="left", padx=(SPACE_3, SPACE_4))

        self._player_dot(self.hud, player, 15)
        tk.Label(
            self.hud, text=self._player_name(player), fg=ACCENT,
            bg=PANEL_BACKGROUND, font=serif(SIZE_BODY, "bold"),
        ).pack(side="left", padx=(0, SPACE_4))

        tk.Label(
            self.hud,
            text=f"{player.sestertii} sestertii   ·   "
                 f"{player.houses} houses",
            fg=TEXT_COLOR, bg=PANEL_BACKGROUND, font=sans(SIZE_SMALL),
        ).pack(side="left", padx=(0, SPACE_4))

        self._draw_marker(player)
        self._draw_goods(player)
        self._draw_whose_turn(self._person)

    @property
    def _person(self) -> Player | None:
        """The player the human is playing."""
        return next(
            (player for player in self.game.players
             if isinstance(player, HumanPlayer)),
            None,
        )

    def _draw_whose_turn(self, person: Player | None) -> None:
        """
        Say whose turn it is, at the right of the band.

        :param person: The seat played by hand, None when the AI plays them
            all, in which case no turn is anybody's own.
        """
        playing = self.game.next_player

        if playing is None:
            return

        if person is not None and playing is person:
            tk.Label(
                self.hud, text="YOUR TURN", fg=ACCENT_INK, bg=ACCENT,
                font=sans(SIZE_MICRO, "bold"), padx=SPACE_2, pady=1,
            ).pack(side="right", padx=(SPACE_2, SPACE_3), pady=SPACE_1)
            return

        box = tk.Frame(self.hud, bg=PANEL_RAISED)
        box.pack(side="right", padx=(SPACE_2, SPACE_3), pady=SPACE_1)
        self._player_dot(box, playing, 11, ground=PANEL_RAISED)
        tk.Label(
            box, text=f"{self._player_name(playing)} is playing",
            fg=MUTED_COLOR, bg=PANEL_RAISED, font=sans(SIZE_MICRO),
        ).pack(side="left", padx=(0, SPACE_2))

    def _draw_marker(self, player: Player) -> None:
        """Pin the PRÆFECTVS MAGNVS in the band, beside whoever holds it."""
        card = player.praefectus_magnus

        if not player.has_praefectus_magnus or card is None:
            return

        tile = tk.Canvas(
            self.hud, width=MARKER_WIDTH, height=MARKER_HEIGHT,
            bg=PANEL_BACKGROUND, highlightthickness=0, cursor="hand2",
        )
        tile.pack(side="left", padx=(0, SPACE_2))
        self._draw_marker_tile(tile, card)
        tile.bind("<Button-1>", lambda _e: self._select(card, playable=False))

        # The band is already full with five players and five goods, so the
        # caption is dropped.
        flag = tk.Label(
            self.hud, text="×2 BONUS", fg=HIGHLIGHT, bg=PANEL_BACKGROUND,
            font=sans(SIZE_MICRO, "bold"), cursor="hand2",
        )
        flag.pack(side="left", padx=(0, SPACE_4))
        flag.bind("<Button-1>", lambda _e: self._select(card, playable=False))

    @staticmethod
    def _draw_marker_tile(tile: tk.Canvas, card: Card) -> None:
        """
        Draw the tile's own picture, or a gold plate standing in for it.

        :param tile: The canvas the tile is drawn on.
        :param card: The PRÆFECTVS MAGNVS card.
        """
        photo = card_photo(card, MARKER_WIDTH, MARKER_HEIGHT, MARKER_RADIUS)

        if photo is not None:
            tile.create_image(
                MARKER_WIDTH / 2, MARKER_HEIGHT / 2, image=photo,
            )
            return

        draw_rounded_rect(
            tile, 1, 1, MARKER_WIDTH - 1, MARKER_HEIGHT - 1, MARKER_RADIUS,
            "marker", fill=ACCENT, outline=CARD_BORDER, width=1,
        )
        tile.create_text(
            MARKER_WIDTH / 2, MARKER_HEIGHT / 2, text="PM",
            font=serif(SIZE_BODY, "bold"), fill=ACCENT_INK,
        )

    def _draw_goods(self, player: Player) -> None:
        """Show the storehouse as one chip per good, held or run out."""
        # The band only holds the human storehouse, so an AI question lights
        # the rail instead.
        offered = (
            () if self.is_watching
            else highlight.goods_for(self.play.request)
        )
        takes_a_click = not self.is_watching
        shelf = storehouse_shelf(
            self.game.goods_by_name.values(), player.storehouse
        )

        tk.Label(
            self.hud, text="STOREHOUSE", fg=MUTED_COLOR,
            bg=PANEL_BACKGROUND, font=sans(SIZE_MICRO, "bold"),
        ).pack(side="left", padx=(0, SPACE_2))

        if not shelf:
            tk.Label(
                self.hud, text="empty", fg=MUTED_COLOR,
                bg=PANEL_BACKGROUND, font=sans(SIZE_MICRO, "italic"),
            ).pack(side="left")
            return

        for name, count in shelf:
            self._draw_chip(name, count, name in offered, takes_a_click)

    def _draw_chip(self, name: str, count: int, wanted: bool,
                   takes_a_click: bool = True) -> None:
        """
        One good of the storehouse: its colour, its initial and its count.

        :param name: The good's name, as the ORDB spells it.
        :param count: How many are held.
        :param wanted: Whether the running action is asking for this good,
            which rims it in gold.
        :param takes_a_click: Whether clicking it answers the question, which
            it does not while an AI seat is the one being asked.
        """
        good = self.game.get_good(name)
        color = good.color if good else "#8a8a8a"
        token = good_photo(name, CHIP_TOKEN, CHIP_TOKEN)
        chip = tk.Canvas(
            self.hud, width=CHIP_SIZE, height=CHIP_SIZE, bg=PANEL_BACKGROUND,
            highlightthickness=0,
            cursor="hand2" if wanted and takes_a_click else "",
        )
        chip.pack(side="left", padx=(0, SPACE_1 // 2))
        draw_rounded_rect(
            chip, 2, 2, CHIP_SIZE - 2, CHIP_SIZE - 2, 4, "chip",
            fill=CARD_FACE if token is not None else color,
            outline=HIGHLIGHT if wanted else color,
            width=3 if wanted else 2,
        )

        if token is not None:
            chip.create_image(CHIP_SIZE / 2, CHIP_SIZE / 2, image=token)
        else:
            chip.create_text(
                CHIP_SIZE / 2, CHIP_SIZE / 2, text=name[0].upper(),
                font=sans(SIZE_MICRO, "bold"), fill=ink_on(color),
            )

        if wanted:
            if takes_a_click:
                chip.bind("<Button-1>", lambda _e: self._answer(name))

        # A count of none is written, but faintly, so the eye skips it.
        tk.Label(
            self.hud, text=f"×{count}",
            fg=HIGHLIGHT if wanted else TEXT_COLOR if count else MUTED_COLOR,
            bg=PANEL_BACKGROUND, font=sans(SIZE_MICRO, "bold"),
        ).pack(side="left", padx=(0, SPACE_3))

    @staticmethod
    def _player_dot(parent: tk.Widget, player: Player, size: int,
                    side: str = "left",
                    ground: str = PANEL_BACKGROUND) -> None:
        """Draw a player's colour as a dot."""
        dot = tk.Canvas(
            parent, width=size, height=size, bg=ground,
            highlightthickness=0,
        )
        dot.pack(side=side, padx=(SPACE_2, SPACE_1 + 2))
        dot.create_oval(
            1, 1, size - 1, size - 1, fill=player.color, outline=TEXT_COLOR
        )

    # --- Pointer ---

    def _on_click(self, event: tk.Event) -> None:
        """Route a click, nearest the eye first."""
        if self._end.is_open:
            self._end.hide()
            return

        if self._detail.is_open:
            self._detail.hide()
            return

        if self.is_watching:
            # An AI is playing: its options are lit to be read, not to be
            # clicked.
            return

        if self.play.is_running:
            self._answer_click(event.x, event.y)
            return

        card = self.hand.card_at(event.x, event.y)
        if card is not None:
            self._select(card, playable=True)
            return

        card = self.market.card_at(event.x, event.y)
        if card is not None:
            self._select(card, playable=False)
            return

        city = self._city_at(event.x, event.y)
        if city is not None:
            self._show_city(city)

    def _answer_click(self, x: float, y: float) -> None:
        """
        Answer the running action with whatever was clicked.

        :param x: The pointer's x, in canvas coordinates.
        :param y: The pointer's y, in canvas coordinates.
        """
        if self.choices.click_at(x, y):
            return

        request = self.play.request
        routes = highlight.routes_for(request)

        for found, offered in (
                (self._offer_at(x, y), highlight.discards_for(request)),
                (self._colonist_at(x, y), highlight.colonists_for(request)),
                (self.market.highlighted_card_at(x, y),
                 highlight.market_cards_for(request)),
                (self._province_at(x, y), highlight.provinces_for(request)),
                (self._city_at(x, y), highlight.cities_for(request)),
                (self._route_at(x, y, routes), routes),
        ):
            if found is not None and found in offered:
                self._answer(found)
                return

    def _on_motion(self, event: tk.Event) -> None:
        """Raise the card of the hand the pointer is on."""
        if not self._detail.is_open and not self.play.is_running:
            self.hand.hover_at(event.x, event.y)

    def _escape(self) -> None:
        """Close whatever is open: the end screen, the panel, then the card."""
        if self._end.is_open:
            self._end.hide()
        elif self._detail.is_open:
            self._detail.hide()
        elif self.play.is_running and not self.is_watching:
            self._cancel()

    # --- Cards ---

    def _select(self, card: Card, playable: bool) -> None:
        """
        Open a card over the table and mark it wherever it is drawn.

        :param card: The clicked card.
        :param playable: Whether the card sits in the current hand.
        """
        player = self.game.next_player
        self.hand.set_selected(card)
        self.market.set_selected(card)
        # Every card can be played even when it does nothing: the rules allow
        # it, and it puts the card on the discard pile for a DIPLOMAT.
        self._detail.show(
            card, playable,
            enabled=(playable
                     and player is not None
                     and not self.game.is_over
                     and isinstance(player, HumanPlayer)
                     and card in player.hand),
        )

    def _clear_selection(self) -> None:
        """Drop the selection when the detail panel closes."""
        self.hand.set_selected(None)
        self.market.set_selected(None)

    def _play(self, card: Card) -> None:
        """
        Start a card of the current hand, and light up what it asks for.

        :param card: The card to play.
        """
        player = self.game.next_player

        if self.game.is_over:
            self._status.set("The game is over.")
            return

        if self.play.is_running:
            self._status.set("Answer the question on the table first.")
            return

        if not isinstance(player, HumanPlayer):
            self._status.set("Not your turn yet.")
            return

        if card not in player.hand:
            self._status.set(f"{card.name} is not in the current hand.")
            return

        self._detail.hide()
        self._clear_selection()

        flow = self.cards.flow(card, player)

        if flow is None:
            self._status.set(f"{card.name} has no action implemented yet.")
            return

        # The place the card was taken from, so a cancelled card goes back
        # there.
        self._laid_from = player.hand.index(card)
        self.cards.lay_down(card, player)
        # Taken with the card already on the pile, so _cancel only undoes the
        # action.
        self._laid_down = effects.snapshot(self.game)
        self._settle(self.play.start(card, flow))

    def _answer(self, value) -> None:
        """Send an answer back to the card being played."""
        if not self.play.is_running:
            return

        self._settle(self.play.answer(value))

    def _cancel(self) -> None:
        """
        Stop the card being played, and take it back where nothing was done.
        """
        card = self.play.card
        player = self.game.next_player

        if card is None:
            self._status.set("Nothing to stop.")
            return

        self.play.cancel()

        if player is None or not self._can_take_back():
            self._finish_turn(
                f"{card.name} had already acted, so it stays played "
                f"and the turn is over."
            )
            return

        self.cards.take_back(card, player, self._laid_from)
        self._laid_down = None
        self.played.hide()
        self._status.set(f"{card.name} goes back to your hand. "
                         f"Pick another card.")
        self.refresh()

    def _can_take_back(self) -> bool:
        """Whether the card being played has changed nothing yet."""
        return (
            self._laid_down is not None
            and effects.untouched(
                self._laid_down,
                effects.snapshot(self.game),
            )
        )

    def _way_out(self) -> str:
        """What the button leaving the card behind should read."""
        if self._can_take_back():
            return CANCEL_LABEL

        return GIVE_UP_LABEL

    @staticmethod
    def _hint_for(request) -> str:
        """What the player has to do to answer the current question."""
        if highlight.is_control(request):
            return "Answer with the buttons below the map."
        if highlight.discards_for(request):
            return "Click one of the cards laid out over the map."
        if highlight.market_cards_for(request):
            return "Click one of the market cards ringed in gold."
        if highlight.goods_for(request):
            return "Click one of the goods rimmed in gold, down in the bar."
        if highlight.colonists_for(request):
            return "Click one of the colonists ringed in gold."
        if highlight.routes_for(request):
            return "Click one of the roads traced in gold."
        if highlight.provinces_for(request):
            return "Click one of the markers ringed in gold."
        if highlight.cities_for(request):
            return "Click one of the cities ringed in gold."
        return ("Escape stops the card, which comes back to your hand "
                "while it has done nothing yet.")

    def _settle(self, request) -> None:
        """
        Redraw for wherever the action came to rest, and end the turn when it
        has run out of questions.
        """
        if request is not None:
            self._status.set(self._hint_for(request))
            self.refresh()
            return

        self._end_turn()

    # --- Turns ---

    def _end_turn(self) -> None:
        """Note what the card just played did, and pass the turn on."""
        player = self.game.next_player
        card = self.play.card
        played = self.play.result
        said = "Your turn is over."

        if player is not None and card is not None:
            said = (
                f"{self._player_name(player)} played {card.name}." if played
                else f"{card.name} found nothing to do."
            )

        self.play.cancel()
        self._finish_turn(said, acted=bool(played))

    def _finish_turn(self, said: str, acted: bool = True) -> None:
        """
        Close the seat's turn: award the CONCORDIA card if this turn ended the
        game, hand the table on, and set the AI seats going.

        :param said: What to put in the status bar for the turn just played.
        :param acted: Whether the card played carried its action out. Two
            whole rounds of turns that did not means the table can reach
            neither end of the game, which the rules do not describe and which
            would otherwise pass the seats round for ever.
        """
        player = self.game.next_player

        if player is None:
            self.refresh()
            return

        self._laid_down = None
        self._idle_turns = 0 if acted else self._idle_turns + 1

        if self.game.trigger_end_if_due(player):
            said = (
                f"{self._player_name(player)} takes the CONCORDIA card, "
                f"every other player has one turn left."
            )

        self._status.set(said)
        self.game.close_turn(player)
        self.refresh()

        if self._idle_turns >= 2 * len(self.game.players):
            self.game.is_over = True

        if self.game.is_over:
            self._show_final_scores()
            return

        self._later(BETWEEN_TURNS_MS, self._play_ai_turn)

    def _show_final_scores(self) -> None:
        """
        Tally the game, then put the standings over the board and in the
        status bar, which keeps them once the screen is closed.
        """
        scores = ScoreManager(self.game)
        standings = scores.ranking()

        if not standings:
            self._status.set("The game is over.")
        else:
            winner, best = standings[0]
            table = " · ".join(
                f"{self._player_name(seat)} {victory_points}"
                for seat, victory_points in standings
            )
            self._status.set(
                f"Game over, {self._player_name(winner)} wins with "
                f"{best} VP.  {table}"
            )

        self._detail.hide()
        self.played.hide()
        self.refresh()
        self._end.show(
            screen_title(self.game.description),
            standings_rows(standings, self._player_name),
            credits_lines(self.game.description),
        )

    def _turn_hint(self) -> str:
        """What to say to the human player when their turn starts."""
        if self._doubles_the_bonus():
            return f"{TURN_HINT}  {MARKER_HINT}"
        return TURN_HINT

    # --- The turn of an AI player, shown on the window ---

    def _later(self, delay: int, then) -> None:
        """
        Do something after a pause, keeping hold of the timer.

        :param delay: How long to wait, in milliseconds.
        :param then: What to do afterwards.
        """
        self._cancel_later()
        self._ai_job = self.canvas.after(delay, then)

    def _cancel_later(self) -> None:
        """Drop the outstanding AI timer, if there is one."""
        if self._ai_job is not None:
            self.canvas.after_cancel(self._ai_job)
            self._ai_job = None

    def _skip_ai_turn(self) -> None:
        """Finish the AI turn now, without watching the rest of it."""
        if self._ai is None:
            return

        self._skipping = True
        self._cancel_later()
        self.canvas.delete(ANIM_TAG)
        self._resolve_ai_turn()

    def _play_ai_turn(self) -> None:
        """Start the turn of an AI player and show the card it plays."""
        self._cancel_later()
        self._skipping = False
        player = self.game.next_player

        if player is None or self.game.is_over:
            self.played.hide()
            self._show_final_scores()
            return

        if isinstance(player, HumanPlayer):
            self.played.hide()
            self._status.set(self._turn_hint())
            self.refresh()
            return

        # A playable card is preferred, but one is always played: passing is
        # not allowed.
        choices = [
                      card for card in player.hand
                      if self.cards.is_playable(card, player)
                  ] or list(player.hand)

        if not choices:
            self.played.hide()
            self._finish_turn(
                f"{self._player_name(player)} had no card left to play.",
                acted=False,
            )
            return

        card = player.choose_card(choices, self.game)
        flow = self.cards.flow(card, player)

        if flow is None:
            self.cards.lay_down(card, player)
            self.played.hide()
            self._finish_turn(
                f"{self._player_name(player)} played {card.name}, which "
                f"the game has no action for.",
                acted=False,
            )
            return

        self._ai = AiAnswerer(self.game, player)
        self.cards.lay_down(card, player)
        self._laid_down = None
        self.played.show(
            card, self._player_name(player), player.color,
        )
        self._status.set(
            f"{self._player_name(player)} plays {card.name}."
        )
        self._settle_ai(self.play.start(card, flow))

    def _settle_ai(self, request) -> None:
        """
        Show what the AI is deciding, then leave it standing there a beat.
        """
        if request is None:
            self._end_ai_turn()
            return

        if self._skipping or not self._pause:
            self._resolve_ai_turn()
            return

        self.refresh()
        # The prompt of the request, not _hint_for, which tells a person where
        # to click.
        self._status.set(f"{self._who_is_playing()} {request.prompt}")
        self._later(self._pause, self._answer_as_ai)

    def _answer_as_ai(self) -> None:
        """Let the AI answer what it was standing at, and show what changed."""
        request = self.play.request

        if self._ai is None or request is None:
            self._end_ai_turn()
            return

        before = effects.snapshot(self.game)
        following = self.play.answer(self._ai(request))
        done = effects.changes(before, effects.snapshot(self.game))

        self._animate(done, lambda: self._settle_ai(following))

    def _resolve_ai_turn(self) -> None:
        """
        Play the rest of the card out at once, and animate the whole of it.
        """
        before = effects.snapshot(self.game)

        while self.play.is_running and self._ai is not None:
            request = self.play.request

            if request is None:
                break

            self.play.answer(self._ai(request))

        done = effects.changes(before, effects.snapshot(self.game))
        self._animate(done, self._end_ai_turn)

    def _end_ai_turn(self) -> None:
        """Close the turn of the AI player and start the next one."""
        self.canvas.delete(ANIM_TAG)
        self._ai = None
        self.played.hide()
        self._end_turn()

    def _who_is_playing(self) -> str:
        """The name of the player whose turn it is, for the status bar."""
        player = self.game.next_player

        return "" if player is None else f"{self._player_name(player)},"

    # --- Showing what a decision did ---

    def _animate(self, done: list, then) -> None:
        """
        Play the outcomes of one decision out on the map, then carry on.

        :param done: What changed, from `views.effects`.
        :param then: What to do once the marks have played out.
        """
        self.refresh()

        if done:
            self.played.set_caption(effects.caption_for(done))

        marks = [] if self._skipping else self._marks_for(done)

        if not marks:
            then()
            return

        self._rise = 0.0
        self._step_marks(marks, 0, then)

    def _step_marks(self, marks: list, frame: int, then) -> None:
        """
        Move every mark one frame on, and clear them at the end.

        :param marks: The (item, dx, dy, grow, cx, cy) of each mark.
        :param frame: Which frame is being drawn.
        :param then: What to do once the last one is drawn.
        """
        if frame >= ANIM_FRAMES or self._skipping:
            self.canvas.delete(ANIM_TAG)
            then()
            return

        eased = ease_out_cubic((frame + 1) / ANIM_FRAMES)
        step = eased - self._rise
        self._rise = eased

        for item, dx, dy, grow, cx, cy in marks:
            self.canvas.move(item, dx * step, dy * step)

            if grow:
                # The ring grows around its centre, so it does not slide away.
                spread = (1 + grow * eased) / (1 + grow * (eased - step))
                self.canvas.scale(item, cx, cy, spread, spread)

        self._later(
            FRAME_MS, lambda: self._step_marks(marks, frame + 1, then)
        )

    def _marks_for(self, done: list) -> list:
        """The canvas items that say what just happened, and how they move."""
        marks: list = []
        ledger: list[tuple[str, str]] = []
        acting = self.game.next_player

        for effect in done:
            if isinstance(effect, effects.ColonistMoved):
                marks += self._mark_move(effect)
            elif isinstance(effect, effects.HouseBuilt):
                marks += self._mark_house(effect)
            elif isinstance(effect, effects.CardBought):
                ledger.append((HIGHLIGHT, effect.caption))
            elif getattr(effect, "player", None) is acting:
                ledger.append(self._ledger_line(effect))

        return marks + self._mark_ledger(
            [line for line in ledger if line is not None]
        )

    def _ledger_line(self, effect) -> tuple[str, str] | None:
        """The colour and the text of one goods or money effect."""
        if isinstance(effect, effects.GoodsGained):
            color = self._good_color(effect.good) or HIGHLIGHT
            return color, f"+{effect.count} {effect.good}"

        if isinstance(effect, effects.GoodsLost):
            color = self._good_color(effect.good) or MUTED_COLOR
            return MUTED_COLOR, f"−{effect.count} {effect.good}"

        if isinstance(effect, effects.MoneyChanged):
            sign = "+" if effect.delta > 0 else "−"
            color = HIGHLIGHT if effect.delta > 0 else MUTED_COLOR
            return color, f"{sign}{abs(effect.delta)} sestertii"

        return None

    def _mark_move(self, effect) -> list:
        """A colonist's move: the road it took, and a ring where it arrived."""
        arrived = self._anchor_of(effect.destination)

        if arrived is None:
            return []

        marks = []
        left = self._anchor_of(effect.origin)

        if left is not None and left != arrived:
            self.canvas.create_line(
                *left, *arrived, fill=HIGHLIGHT, width=3, arrow="last",
                capstyle="round", tags=ANIM_TAG,
            )
            travelling = self.canvas.create_oval(
                left[0] - 5, left[1] - 5, left[0] + 5, left[1] + 5,
                fill=HIGHLIGHT, outline=MAP_INK, tags=ANIM_TAG,
            )
            marks.append((
                travelling, arrived[0] - left[0], arrived[1] - left[1],
                0.0, 0.0, 0.0,
            ))

        return marks + [self._ring_at(arrived, HIGHLIGHT)]

    def _mark_house(self, effect) -> list:
        """A house going up: a ring in its builder's colour, opening out."""
        spot = self._points.get(effect.city)

        if spot is None:
            return []

        return [self._ring_at(spot, effect.color or HIGHLIGHT)]

    def _ring_at(self, spot: tuple[float, float], color: str) -> tuple:
        """
        A ring that opens out from a point on the map.

        :param spot: Where to centre it.
        :param color: What colour to draw it.
        :return: The mark for it.
        """
        x, y = spot
        radius = self._p(RING_RADIUS)
        ring = self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline=color, width=HIGHLIGHT_WIDTH, tags=ANIM_TAG,
        )

        return ring, 0.0, 0.0, RING_GROWTH, x, y

    def _mark_ledger(self, lines: list) -> list:
        """
        The goods and the sestertii of a turn, rising off the map's floor.
        """
        left, _top, right, bottom = self._board_rect()
        middle = (left + right) / 2
        marks = []

        for index, (color, said) in enumerate(lines):
            y = bottom - self._p(LABEL_STEP) * (len(lines) - index)
            # A haloed text is nine canvas items, so it gets its own tag to be
            # moved.
            line_tag = f"{ANIM_TAG}-{index}"
            self._haloed_text(
                middle, y, said, sans(SIZE_BODY, "bold"), color, line_tag,
            )
            self.canvas.addtag_withtag(ANIM_TAG, line_tag)
            marks.append(
                (line_tag, 0.0, -self._p(LABEL_RISE), 0.0, 0.0, 0.0)
            )

        return marks

    def _anchor_of(self, position):
        """Where a city or a route is drawn, for a mark to be put on it."""
        if position is None:
            return None

        if isinstance(position, Route):
            polyline = self._curves.get(position)
            return None if polyline is None else midpoint(polyline)

        return self._points.get(position)
