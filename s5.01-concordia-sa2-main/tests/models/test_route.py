"""
File: test_route.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for a route and the colonists standing on it.
"""
from concordia.models.city import City
from concordia.models.colonist import Colonist
from concordia.models.route import Route

ROMA = City("Roma", "A", 3)
OSTIA = City("Ostia", "A", 3)
PISAE = City("Pisae", "A", 3)


def test_route_ends_on_both_cities():
    route = Route(ROMA, OSTIA, "land")

    assert route.cities == (ROMA, OSTIA)
    assert route.touches(ROMA) is True
    assert route.touches(OSTIA) is True
    assert route.touches(PISAE) is False


def test_routes_meeting_at_a_city_are_adjacent():
    left = Route(ROMA, OSTIA, "land")
    right = Route(OSTIA, PISAE, "land")

    assert left.is_adjacent(right) is True
    assert right.is_adjacent(left) is True


def test_placing_a_colonist_moves_it():
    roma = City("Roma", "A", 3)
    road = Route(roma, OSTIA, "land")
    colonist = Colonist("land")

    colonist.place(roma)
    colonist.place(road)

    assert colonist.position is road
    assert colonist.route is road
    assert colonist.city is None
    assert roma.colonists == []
    assert road.colonists == [colonist]
