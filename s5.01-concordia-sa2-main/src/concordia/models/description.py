"""
File: description.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: The box description of the game, as ccd_description holds it.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameDescription:
    """What the box says about the game: who made it and who it is for."""

    name: str
    edition_year: int | None = None
    designer: str | None = None
    publisher: str | None = None
    players: str | None = None
    age: str | None = None
    playing_time: int | None = None
    artists: tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        credits_line = self.designer or "unknown designer"
        if self.artists:
            credits_line += f", art by {', '.join(self.artists)}"
        return (
            f"{self.name} ({self.edition_year}) - {credits_line}\n"
            f"{self.publisher} | {self.players} players | "
            f"{self.age}+ | {self.playing_time} min"
        )
