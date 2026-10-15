"""
File: test_rules.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 09-09-2026
Description: Tests for the rules that are not stored in the database.
"""
import pytest

from concordia.rules import (
    canonical_god, minerva_vp_for, same_god, specialist_good_for,
)


@pytest.mark.parametrize("spelling, expected", [
    ("JVPITER", "jupiter"),
    ("Jupiter", "jupiter"),
    ("SATVRNVS", "saturnus"),
    ("MINERVA", "minerva"),
])
def test_canonical_god(spelling, expected):
    assert canonical_god(spelling) == expected


def test_same_god_across_spellings():
    assert same_god("JVPITER", "Jupiter")
    assert same_god("SATVRNVS", "saturn")
    assert not same_god("MINERVA", "MARS")
    assert not same_god(None, "MARS")


@pytest.mark.parametrize("good, expected", [
    ("cloth", 5), ("CLOTH", 5), ("brick", 3),
])
def test_minerva_vp_for(good, expected):
    assert minerva_vp_for(good) == expected


@pytest.mark.parametrize("card, good", [
    ("MASON", "brick"),
    ("WEAVER", "cloth"),
    ("weaver", "cloth"),
])
def test_specialist_good_for(card, good):
    assert specialist_good_for(card) == good
