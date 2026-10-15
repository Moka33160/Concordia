"""
File: rules.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: The few rules the database schema cannot store, kept in one place.
"""

# MINERVA is worth 3, 4 or 5 points per city depending on the good. The
# column NT_God_CCD.god_victory_points only accepts 1, 2 or 7, so her row is
# NULL in the database and the values are written here.
MINERVA_VP_BY_GOOD = {
    "brick": 3,
    "food": 3,
    "tool": 3,
    "wine": 4,
    "cloth": 5,
}

# The good of each specialist. Only the DIPLOMAT deck stores a good per
# card in the database, so the specialists are listed here.
SPECIALIST_GOOD_BY_CARD = {
    "MASON": "brick",
    "FARMER": "food",
    "SMITH": "tool",
    "VINTNER": "wine",
    "WEAVER": "cloth",
}


# What a colonist costs to place or to buy. The price is not in the
# database, only the starting colonists are.
COLONIST_COST = ("food", "tool")


# The database spells the gods the Roman way, with a V instead of a U:
# JVPITER, SATVRNVS, MERCVRIVS. Every spelling is listed here and folded to
# one key. Replacing every V by a U would not work, it gives "MINERUA".
GOD_ALIASES = {
    "vesta": ("vesta",),
    "jupiter": ("jupiter", "jvpiter", "iupiter", "ivpiter"),
    "saturnus": ("saturnus", "saturn", "satvrnvs", "satvrnus"),
    "mercurius": ("mercurius", "mercury", "mercvrivs", "mercvrius"),
    "mars": ("mars",),
    "minerva": ("minerva", "minerve"),
    "concordia": ("concordia",),
}

_CANONICAL_GOD = {
    alias: canonical
    for canonical, aliases in GOD_ALIASES.items()
    for alias in aliases
}


def canonical_god(name: str | None) -> str | None:
    """Fold a god name onto the one key the rules are written against."""
    if name is None:
        return None
    return _CANONICAL_GOD.get(name.strip().lower())


def same_god(left: str | None, right: str | None) -> bool:
    """
    Whether two names denote the same god, Roman spelling included.

    :param left: The first name.
    :param right: The second name.
    :return: True when both name the same god.
    """
    if left is None or right is None:
        return False
    canonical = canonical_god(left)
    if canonical is None:
        return left.strip().lower() == right.strip().lower()
    return canonical == canonical_god(right)


def minerva_vp_for(good_name: str | None) -> int:
    """
    How many victory points a MINERVA specialist scores per matching city.
    """
    if good_name is None:
        return 0
    return MINERVA_VP_BY_GOOD.get(good_name.lower(), 0)


def specialist_good_for(card_name: str | None) -> str | None:
    """The good a specialist card produces, by card name."""
    if card_name is None:
        return None
    return SPECIALIST_GOOD_BY_CARD.get(card_name.strip().upper())
