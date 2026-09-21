# pylint: disable=expression-not-assigned, multiple-statements
from random import randint, sample
from time import sleep

from grappa import should

from py_microframeworks.bingo import Bingo


def test_bingo_must_find_an_appropriate_activity():
    state = {"month": randint(1, 12), "wind": randint(0, 25), "temp": 0, "snowdepth": 0,
             "activities": ["flyfishing", "iceskating", "sailing", "skiing"]}
    def warm_period():
        return state["month"] in [4, 5, 6, 7, 8, 9, 10]
    def get_temp():
        temp_range = (6, 30) if warm_period() else (-35, 5)
        state["temp"] = randint(*temp_range); return True
    def get_snow():
        state["snowdepth"] = 0 if warm_period() else randint(0, 120); return True
    def drop_activity(activity):
        state["activities"].remove(activity)
    def add_activity(activity):
        state["activities"].append(activity)
    def pick_one():
        state["activities"] = sample(state["activities"], 1)

    board = Bingo(state, lambda: sleep(0.01), max_iterations=3)

    board.add_cell(get_temp, get_snow)
    board.add_cell("temp < 10 or wind < 6", callback=lambda: drop_activity("sailing"))
    board.add_cell("snowdepth < 40", callback=lambda: drop_activity("skiing"))
    board.add_cell("temp > 5 or snowdepth > 10", callback=lambda: drop_activity("iceskating"))
    board.add_cell("any([wind > 6, temp < 5, snowdepth > 1])",
                   callback=lambda: drop_activity("flyfishing"))
    board.add_cell("len(activities) == 1", callback=board.stop)
    board.add_cell("remaining_iterations == 1", "len(activities) == 0",
                   callback=lambda: add_activity("cards"))
    board.add_cell("remaining_iterations == 1", "len(activities) > 1",
                   callback=pick_one)

    board.wait()

    len(state["activities"]) | should.be.equal.to(1)
