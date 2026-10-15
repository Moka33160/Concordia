"""
File: test_requests.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the requests an action asks and the answers they accept.
"""
from concordia.actions.requests import ChooseAmount, ChooseCity


def test_request_accepts_an_offered_answer():
    request = ChooseCity("Where to?", options=("Roma", "Aquileia"))

    assert request.accepts("Roma")


def test_request_refuses_an_unknown_answer():
    request = ChooseCity("Where to?", options=("Roma", "Aquileia"))

    assert not request.accepts("Carthago")


def test_amount_accepts_a_value_in_bounds():
    request = ChooseAmount("How many?", minimum=1, maximum=3)

    assert request.accepts(1)
    assert request.accepts(3)
