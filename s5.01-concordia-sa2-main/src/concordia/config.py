"""
File: config.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: The game configuration (debug, map, number of players, color)
"""
import random
import sys
from collections.abc import Iterable

from concordia.db.database_controller import DatabaseController


class GameConfig:
    """Game configuration"""

    debug: bool = False
    nb_players: int = 0
    map: str = ""
    color: str = ""
    # The seat the person sits at, None when the AI plays every one of them.
    human_position: int | None = 0
    auto: bool = False

    def __init__(self, argv: list[str], dbc: DatabaseController):
        self.argv = argv
        self.player_limits = dbc.get_map_player_limits()
        self.player_colors = dbc.get_player_colors()
        self.parse_arguments(argv)

    def parse_arguments(self, argv: list[str]) -> None:
        """
        Parse the command line arguments
        This is done in 4 steps:
            - Check if the map is valid
            - Check if the number of players is valid for the map
            - Check if the color is valid, else use random
            - Pick the seat the human player sits at, unless the AI plays
              them all

        :param argv: The command line arguments
        """
        # 0. Show the usage and stop if help is requested
        if "-h" in argv or "--help" in argv:
            self.usage()
            sys.exit(0)

        # 1. Check if the map is valid (case-insensitive), else raise an error
        map_name = argv[argv.index("-m") + 1] if "-m" in argv else ""
        resolved_map = self._resolve_option(map_name, self.player_limits)
        if resolved_map is None:
            raise ValueError(
                f"Unknown map {map_name!r}, pick one of "
                f"{', '.join(self.player_limits)}"
            )
        map_name = resolved_map

        # 2. Check if the number of players is valid for the map, else
        # raise an error. If no number of players is specified, pick a
        # random one within range
        minimum, maximum = self.player_limits[map_name]
        if "-p" in argv:
            nb_players = int(argv[argv.index("-p") + 1])
        else:
            nb_players = random.randint(minimum, maximum)
        if not minimum <= nb_players <= maximum:
            raise ValueError(
                f"{map_name} takes {minimum} to {maximum} players, "
                f"got {nb_players}"
            )

        # 3. Check if the color is valid (case-insensitive), else use
        # random. With every seat played by the AI there is no colour to
        # reserve, so the whole pool stays open to them.
        auto = "-a" in argv or "--auto" in argv
        if auto and "-c" in argv:
            raise ValueError(
                "-c has no meaning with --auto: no seat is played by hand"
            )

        color = ""
        if not auto:
            color = argv[argv.index("-c") + 1] if "-c" in argv else ""
            if not color:
                color = random.choice(self.player_colors)
            else:
                resolved_color = self._resolve_option(
                    color, self.player_colors
                )
                if resolved_color is None:
                    raise ValueError(
                        f"Unknown color {color!r}, pick one of "
                        f"{', '.join(self.player_colors)}"
                    )
                color = resolved_color

        # 4. Save the configuration
        self.nb_players = nb_players
        self.map = map_name
        self.color = color
        self.auto = auto
        # No seat belongs to a person when the AI plays the whole table.
        self.human_position = None if auto else random.randrange(nb_players)

    @staticmethod
    def _resolve_option(value: str, options: Iterable[str]) -> str | None:
        """
        Case-insensitively match value against options, returning the option
        with its original casing, or None if there is no match.

        :param value: The user-provided value to resolve
        :param options: The valid options to match against
        :return: The matching option, or None if value matches none of them
        """
        matches = (
            option for option in options if option.lower() == value.lower()
        )
        return next(matches, None)

    def usage(self) -> None:
        """Print the usage message."""
        print(
            "Usage: python3 -m concordia [-m map] [-p nb_players] "
            "[-c color] [-a] [-h]\n"
            "  -m map: The map to play on (obligate, must be one of the maps\n"
            "     in the database)\n"
            "  -p nb_players: The number of players (default: random,\n"
            "     between the minimum and maximum for the chosen map)\n"
            "  -c color: The color of the human player (default: random)\n"
            "  -a, --auto: Let the AI play every seat and watch the game\n"
            "     play itself out. Cannot be used with -c, since no seat\n"
            "     is played by hand.\n"
            "  -h, --help: Show this help message and exit\n\n"
            f"Available maps: {', '.join(self.player_limits)}\n"
            f"Available colors: {', '.join(self.player_colors)}"
        )
