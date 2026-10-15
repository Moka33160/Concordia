"""
File: test_prefect.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 10-09-2026
Description: Tests for the PREFECT action: produce in a province, or collect.
"""
from unittest.mock import MagicMock

from concordia.actions import prefect
from concordia.actions.context import ActionContext
from concordia.models.card import Card, CardOrigin
from concordia.models.city import City
from concordia.models.player import AIPlayer
from concordia.models.province import Province
from concordia.models.resource import Good
from concordia.models.token import BonusMarker, CityToken
from tests.actions.flows import first, option, run

CLOTH = Good("cloth", 7, "#3b5f9e", 4, 5)
BRICK = Good("brick", 3, "#8b5a2b", 2, 1)

PRODUCE = option("produce")
COLLECT = option("collect")


def make_city(name, good, houses=()):
    """A city with a revealed token and the houses already built."""
    city = City(name, "A", 3)
    city.set_token(CityToken("A", good))
    city.houses = list(houses)
    return city


def make_province(name, cities, marker=CLOTH, flipped=False):
    """A province with those cities, and a bonus marker if given one."""
    province = Province(name, "I")
    for city in cities:
        province.add_city(city)
    if marker is not None:
        province.set_bonus_marker(BonusMarker(marker))
    province.is_flipped = flipped
    return province


def make_ctx(player, provinces, others=()):
    """That player playing PREFECT on a board of those provinces."""
    game_state = MagicMock()
    game_state.board.provinces = list(provinces)
    game_state.players = [player, *others]

    by_color = {seat.color: seat for seat in game_state.players}
    game_state.get_player_by_color.side_effect = by_color.get

    card = Card("PREFECT", None, "...", CardOrigin.STARTING)
    return ActionContext(card, player, game_state)


def test_produce_gives_one_good_per_house():
    player = AIPlayer("red")
    province = make_province("Italia", [
        make_city("Roma", BRICK, houses=["red", "red"]),
        make_city("Ostia", CLOTH, houses=["red"]),
    ])

    result, script = run(
        prefect.play(make_ctx(player, [province])), PRODUCE, first
    )

    assert result is True
    assert script.asked == ["ChooseOption", "ChooseProvince"]
    # Two bricks for the two houses, one cloth for the third, and one more
    # cloth for the province's own bonus marker.
    assert player.storehouse == {"brick": 2, "cloth": 2}


def test_produce_turns_the_marker():
    player = AIPlayer("red")
    province = make_province("Italia", [make_city("Roma", BRICK)])

    run(prefect.play(make_ctx(player, [province])), PRODUCE, first)

    assert province.is_flipped is True


def test_praefectus_magnus_doubles_the_bonus():
    player = AIPlayer("red")
    rival = AIPlayer("blue")
    marker_card = Card("PRÆFECTVS MAGNVS", None, "...", CardOrigin.AWARD)
    player.give_praefectus_magnus(marker_card)
    province = make_province("Italia", [], marker=CLOTH)
    ctx = make_ctx(player, [province], [rival])
    ctx.game_state.pass_praefectus_magnus.side_effect = (
        lambda current: rival.give_praefectus_magnus(marker_card)
    )

    run(prefect.play(ctx), PRODUCE, first)

    assert player.storehouse == {"cloth": 2}
    assert rival.has_praefectus_magnus is True


def test_collect_cashes_the_turned_markers():
    player = AIPlayer("red")
    turned = [
        make_province("Italia", [], marker=CLOTH, flipped=True),
        make_province("Gallia", [], marker=BRICK, flipped=True),
    ]

    result, script = run(prefect.play(make_ctx(player, turned)), COLLECT)

    assert result is True
    assert script.asked == ["ChooseOption"]
    assert player.sestertii == CLOTH.bonus_sestertii + BRICK.bonus_sestertii
    assert [province.is_flipped for province in turned] == [False, False]
