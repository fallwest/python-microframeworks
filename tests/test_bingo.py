from time import sleep
from unittest import mock

from grappa import should

from python_microframeworks.bingo import Bingo


def test_bingo_must_call_callback_when_match():
    state = {"a": 1, "b": 1}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a + b == 3", callback=callback)
    board.run()
    state["a"] += 1
    sleep(0.1)
    board.stop()
    callback.called | should.be.true  # pylint: disable=W0104


def test_bingo_must_call_callback_when_multi_condition_cell_match():
    state = {"a": 1, "b": 1, "c": 3}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a + b == 3", "c < 3", callback=callback)
    board.run()
    state["a"] += 1
    sleep(0.1)
    state["c"] -= 1
    sleep(0.1)
    board.stop()
    callback.called | should.be.true  # pylint: disable=W0104


def test_bingo_when_multiple_cells():
    state = {"a": 1, "b": 1}
    callback_0 = mock.Mock()
    callback_1 = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a + b < 3", callback=callback_0)
    board.add_cell("a + b == 3", callback=callback_1)
    board.run()
    state["a"] += 1
    sleep(0.1)
    board.stop()
    all([callback_0.called, callback_1.called]) | should.be.true  # pylint: disable=W0104


def test_bingo_cell_callback_only_called_once():
    state = {"a": 1, "b": 1}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a + b == 3", callback=callback)
    board.run()
    state["a"] += 1
    sleep(0.1)
    state["a"] += 1
    sleep(0.1)
    board.stop()
    callback.call_count | should.be.equal.to(1)  # pylint: disable=W0104


def test_bingo_cell_must_support_object_expressions():
    state = {"a": mock.Mock(call_count=0)}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a.call_count == 2", callback=callback)
    board.run()
    state["a"].call_count += 1
    sleep(0.1)
    state["a"].call_count += 1
    sleep(0.1)
    board.stop()
    callback.called | should.be.true  # pylint: disable=W0104


def test_bingo_cell_must_support_function_in_cell():
    state = {"a": 0}
    callback = mock.Mock()
    def func_to_use():
        return state["a"] > 0
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell(func_to_use, callback=callback)
    board.run()
    state["a"] += 1
    sleep(0.1)
    board.stop()
    callback.called | should.be.true  # pylint: disable=W0104


def test_bingo_cell_must_support_state_change_cell_function_call():
    state = {"a": 0, "func_to_use": lambda: func_to_use()}  # pylint: disable=unnecessary-lambda
    def func_to_use():
        state["a"] += 1
        return True
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell(func_to_use)
    board.add_cell("a==2 or func_to_use()")
    board.wait()
    state["a"] | should.be.equal.to(2)  # pylint: disable=W0104
    # Zero-based
    board.current_iteration | should.be.equal.to(1)


def test_bingo_cell_must_support_state_change_cell_function_call_expr():
    state = {"a": 0, "func_to_use": lambda: func_to_use()}  # pylint: disable=unnecessary-lambda
    def func_to_use():
        state["a"] += 1
        return True
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell(func_to_use, "a==2")
    board.wait()
    state["a"] | should.be.equal.to(2)  # pylint: disable=W0104
    # Zero-based
    board.current_iteration | should.be.equal.to(2)


def test_bing_must_print_error_when_cell_not_callable():
    not_callable = 1
    log_delegate = mock.Mock()
    callback = mock.Mock()
    state = {"a": 0}
    board = Bingo(state, lambda: sleep(0.03), log_delegate=log_delegate)
    board.add_cell(not_callable, callback=callback)
    board.run()
    log_delegate.assert_called_with("Failed to evaluate expressions: (1,). Got exception\nExpression must be a str or callable, got int")
    board.stop()


def test_bingo_cell_must_support_object_function_call_expressions():
    state = {"a": 1, "b": mock.Mock(do_exec=mock.Mock(return_value=True))}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a == 2", "b.do_exec()", callback=callback)
    board.run()
    sleep(0.1)
    state["a"] += 1
    sleep(0.1)
    board.stop()
    callback.called | should.be.true  # pylint: disable=W0104


def test_bingo_must_stop_when_iterations_run_out():
    state = {"a": 0}
    board = Bingo(state, lambda: sleep(0.05), max_iterations=2)
    board.add_cell("a > 0", callback=mock.Mock())
    board.wait(poll=0.2)
    board.running | should.be.false  # pylint: disable=W0104
    board.current_iteration | should.be.higher.than(1)


def test_bingo_must_stop_when_all_cells_are_triggered():
    state = {"a": 0}
    board = Bingo(state, lambda: sleep(0.03), max_iterations=10)
    board.add_cell("a == 1", callback=mock.Mock())
    board.add_cell("a > 0", callback=mock.Mock())
    board.run()
    sleep(0.1)
    state["a"] += 1
    sleep(0.1)
    board.running | should.be.false  # pylint: disable=W0104


def test_bingo_must_not_stop_on_cell_exception():
    state = {"a": 0}
    callback_0 = mock.Mock(side_effect=Exception("boom!"))
    callback_1 = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a == 0", callback=callback_0)
    board.add_cell("a == 1", callback=callback_1)
    board.run()
    sleep(0.1)
    state["a"] += 1
    sleep(0.1)
    board.stop()
    all([callback_0.called, callback_1.called]) | should.be.true  # pylint: disable=W0104


def test_bingo_must_call_cell_repeatedly_when_use_up_false():
    state = {"a": 0}
    callback = mock.Mock()
    board = Bingo(state, lambda: sleep(0.03))
    board.add_cell("a > 0", callback=callback, use_up=False)
    board.run()
    sleep(0.01)
    state["a"] += 1
    sleep(0.01)
    state["a"] += 1
    sleep(0.01)
    state["a"] += 1
    sleep(0.01)
    state["a"] += 1
    sleep(0.01)
    board.stop()
    callback.call_count | should.be.higher.than(1)


def test_bingo_must_call_cells_called_consecutively_when_consecutive():
    state = {"a": 0}
    callback_0 = mock.Mock()
    callback_1 = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05), consecutive=True)
    board.add_cell("a == 2", callback=callback_0)
    board.add_cell("a > 0", callback=callback_1)
    board.run()
    state["a"] += 1
    sleep(0.1)
    callback_1.called | should.be.false  # pylint: disable=W0104
    state["a"] += 1
    sleep(0.1)
    all([callback_0.called, callback_1.called]) | should.be.true  # pylint: disable=W0104


def test_bingo_must_call_cells_in_any_order_when_not_consecutive():
    state = {"a": 0}
    callback_0 = mock.Mock()
    callback_1 = mock.Mock()
    board = Bingo(state, lambda: sleep(0.05))
    board.add_cell("a == 2", callback=callback_0)
    board.add_cell("a > 0", callback=callback_1)
    board.run()
    state["a"] += 1
    sleep(0.1)
    callback_1.called | should.be.true  # pylint: disable=W0104
    state["a"] += 1
    sleep(0.1)
    all([callback_0.called, callback_1.called]) | should.be.true  # pylint: disable=W0104


def test_bingo_must_set_complete_to_true_when_board_completed():
    state = {"a": 1, "b": 1}
    board = Bingo(state, lambda: sleep(0.01))
    board.add_cell("a + b == 3")
    board.run()
    state["a"] += 1
    board.wait()
    board.complete | should.be.true  # pylint: disable=W0104


def test_bingo_must_set_complete_to_true_when_board_completed_when_use_up_false_cell():
    state = {"a": 1, "b": 1}
    board = Bingo(state, lambda: sleep(0.01))
    board.add_cell("a + b == 3")
    board.add_cell("a > 0", use_up=False)
    board.run()
    state["a"] += 1
    board.wait()
    board.complete | should.be.true  # pylint: disable=W0104


def test_bingo_must_set_complete_to_false_when_board_completed_when_use_up_false_cell_not_executed():
    state = {"a": 0}
    board = Bingo(state, lambda: sleep(0.01), max_iterations=5)
    board.add_cell("a > 0")
    board.add_cell("a > 1", use_up=False)
    board.run()
    state["a"] += 1
    board.wait()
    board.complete | should.be.false  # pylint: disable=W0104


def test_bingo_must_set_complete_to_false_when_board_not_completed():
    state = {"a": 0}
    board = Bingo(state, lambda: sleep(0.01), max_iterations=2)
    board.add_cell("a > 0")
    board.wait()
    board.complete | should.be.false  # pylint: disable=W0104
