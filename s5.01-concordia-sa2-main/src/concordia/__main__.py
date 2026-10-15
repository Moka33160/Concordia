"""
File: __main__.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 04-09-2026
Description: Entry point for `python3 -m concordia`.
"""
import sys

from concordia.config import GameConfig
from concordia.controllers.game_controller import GameController
from concordia.db.database_controller import DatabaseController
from concordia.db.database_service import DatabaseService
from concordia.views.game_view import GameView

if __name__ == '__main__':
    # Read the arguments, build the game and open the window.
    dbc = DatabaseController(DatabaseService.from_env())
    config = GameConfig(argv=sys.argv, dbc=dbc)
    ctrl = GameController(config=config, dbc=dbc, autorun=False)

    GameView(ctrl.game).run()

    dbc.close()
