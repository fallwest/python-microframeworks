# python-microframeworks
A collection of functional programming inspired microframeworks for solving complex (even non-linear) problems.

# Frameworks

## The Bingo framework

The Bingo framework allows you to set up a board with cells that get used up when all the function(s) or expression(s) they contain evaluate to `True`. You can specify a callback function to fire when the cell completes. This functional programming inspired micro-framwork is useful for complex and even non-linear sequences that need to continue until one or several criteria are fullfilled. The framework runs through all the cells the number of times specified by the `max_iterations` property (default 5), stopping earlier if all cells are complete.

See [tests/test_integration_bingo.py](tests/test_integration_bingo.py):

```
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
```

## The henrulle framework

The henrulle framework allows you to run through a sequence of functions the number of times specified by the `attempts` parameter (default 2). The framework encourages functional programming conventions: exceptions are suppressed so they do not affect the flow, and all the functions in the sequence should be _pure_ and therefore should not change local state or act upon state changed by another function. An exception to this rule is that a function can always stop the whole sequence by returning `True`.

This framework shines for solving complex workflows when you setup a henrulle sequence of henrulle sequences. In that case you can check in the first function of each subsequence if that sequence is relevant and abort that sequence and hop to the next sequence in the list if it is not.

See [tests/test_task_util.py](tests/test_task_util.py):

```
def test_henrulle_must_attempt_sequence_specified_number_of_times(context_obj):
    task_1 = Mock(return_value=False)
    task_2 = Mock(return_value=False)
    henrulle(context_obj, [task_1, task_2], attempts=3)
    all([task_1.call_count == 3, task_2.call_count == 3]) | should.be.true


def test_henrulle_must_allow_any_task_to_abort_job(context_obj):
    def abort_job():
        context_obj.completed = True
    task_1 = Mock(return_value=False)
    task_2 = Mock(side_effect=abort_job)
    task_3 = Mock(return_value=True)
    henrulle(context_obj, [task_1, task_2, task_3], attempts=1)
    all([task_1.called, task_2.called]) | should.be.true
    task_3.called | should.be.false


def test_henrulle_of_henrulles_must_support_subsequence_behavior():
    task_1_1 = Mock(__name__="task_1_1", return_value=True)
    task_1_2 = Mock(__name__="task_1_2", return_value=False)
    task_2_1 = Mock(__name__="task_1_1", return_value=False)
    task_2_2 = Mock(__name__="task_1_2", return_value=False)

    def sequence_1():
        henrulle(context_obj, [task_1_1, task_1_2], signal="stop-seq1")

    def sequence_2():
        henrulle(context_obj, [task_2_1, task_2_2], signal="stop-seq2")

    henrulle(context_obj, [sequence_1, sequence_2], attempts=1)

    task_1_2.called | should.be.false
    all([task_1_1, task_2_1, task_2_2]) | should.be.true
```
