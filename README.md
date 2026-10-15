<img width="460" height="215" alt="image" src="https://github.com/user-attachments/assets/ec391a07-ef17-439a-ba46-17e4752f30da" />

# Concordia

Python version of the board game *Concordia* (PD-Verlag, Mac Gerdts), made for
the SA2 project of S5.01 (BUT3 Informatique). All the reference data of the
game (maps, cities, routes, cards, setup) is read from an Oracle database, the
rules are in the Python code, and the game is played in a Tkinter window
against AI players.

Group SA2: Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent Paco.

## Requirements

- Python 3.12
- An Oracle database with the Concordia schema (the one of the IUT)
- The dependencies of `pyproject.toml` (oracledb, pillow, python-dotenv, pytest)

We used [uv](https://docs.astral.sh/uv/) for the virtual environment:

```
$ uv sync
```

## Database connection

The connection is read from a `.env` file at the root of the project. Copy
`.env.example` and fill in the password:

```
ORACLE_HOSTNAME=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=IUT12c
ORACLE_USERNAME=ETD
ORACLE_PASSWORD=
```

Nothing works without it: the game reads the whole setup from the database at
start up.

## Launch

```
$ python3 -m concordia -m EU
$ python3 -m concordia -m EU -a
$ python3 -m concordia -h
```

Options:

| Option | What it does |
| --- | --- |
| `-m map` | The map to play on. Required. |
| `-p nb_players` | The number of players. Random inside the limits of the map by default. |
| `-c color` | The colour of the human player. Random by default. |
| `-a` | Only the AI plays. The window opens on a table where every seat is played by the computer and runs to the end on its own. Cannot be used with `-c`. |
| `-h` | Show the help. |

The maps of the database are `Italia` (2-4 players), `Imperium` (3-5) and `EU`
(2-5). The colours are red, green, yellow, blue and black.

## How to play

The human player is one of the players, the others are played by the AI.
With `-a` nobody plays by hand: every seat is the AI's, the window plays the
whole game out on its own and stops on the final standings. Nothing is
clickable but the cards, which can still be opened to read them; the speed
buttons and `Space` work as usual.

- Click a card of your hand to open it, then `Play` to play it.
- The bar drawn on the board says what the card is asking. What can be
  clicked is in gold: a city, a route, a colonist, a good.
- The buttons of that bar answer the questions the board cannot: a choice
  between two branches, an amount, yes or no.
- `Change card` / `Give up card` cancels the card being played. A card that
  did nothing yet goes back to the hand.
- `Escape` closes the card panel, `Space` skips the animation of an AI turn.
  The speed of the AI players is set in the band under the board.

## Project layout

```
src/concordia/
    config.py       command line options
    rules.py        the few rules that are not in the database
    settings.py     Oracle connection settings
    db/             connection to Oracle and the SQL queries
    models/         board, cities, routes, provinces, cards, players, goods
    state/          the state of a game in progress
    controllers/    setup of a game, and the game loop
    managers/       cards and scoring
    actions/        one module per personality card, plus the AI strategy
    views/          the Tkinter interface
assets/             pictures of the cards, the goods and the pieces
tests/              the tests
```

An action is written as a generator: it yields a request (`ChooseCity`,
`ChooseAmount`, `Confirm`, ...) every time it needs a decision and gets the
answer back. The window answers it with the clicks of the player, the AI
answers it with `actions/strategy.py`, and the tests answer it with a script.
This way the rules are written only once.

## Tests

```
$ python3 -m pytest
```

`tests/db/test_database_controller_live.py` reads the real database and is
skipped when nothing answers on the Oracle port. `tests/actions/test_tribune.py`
builds a whole game, so it needs the database too. Everything else runs
offline, on the fake driver of `tests/db/fakes.py` or on the small board of
`tests/fake_game.py`.

## What is missing

- Only one human player, the others are always played by the AI.
- The AI only looks one move ahead, so a colonist never crosses a poor
  province to reach a rich one.
- There is no save: closing the window loses the game.
