# pylint: disable=expression-not-assigned,pointless-statement,redefined-outer-name
import time
from unittest import mock
from unittest.mock import Mock

import pytest
from grappa import should

from py_microframeworks.task_util import henrulle


@pytest.fixture
def context_obj():
    return mock.MagicMock(completed=False)


def test_henrulle_must_do_nothing_when_no_tasks(context_obj):
    henrulle(context_obj, [])
    context_obj.completed | should.be.false


def test_henrulle_must_not_execute_any_tasks_when_job_already_complete(context_obj):
    context_obj.completed = True
    task_1 = Mock(__name__="task_1", return_value=False)
    henrulle(context_obj, [task_1])
    task_1.called | should.be.false


def test_henrulle_must_set_complete_flag_to_true_when_task_returns_true(context_obj):
    henrulle(context_obj, [Mock(__name__="task_1", return_value=True)])
    context_obj.completed | should.be.true


def test_henrulle_must_execute_all_tasks_when_none_return_true(context_obj):
    task_1 = Mock(__name__="task_1", return_value=False)
    task_2 = Mock(__name__="task_2", return_value=False)
    henrulle(context_obj, [task_1, task_2], attempts=1)
    all([task_1.called, task_2.called]) | should.be.true


def test_henrulle_must_not_execute_all_tasks_when_previous_task_returned_true(context_obj):
    task_1 = Mock(__name__="task_1", return_value=False)
    task_2 = Mock(__name__="task_2", return_value=True)
    task_3 = Mock(__name__="task_3", return_value=False)
    henrulle(context_obj, [task_1, task_2, task_3], attempts=1)
    all([task_1.called, task_2.called]) | should.be.true
    task_3.called | should.be.false


def test_henrulle_must_execute_all_tasks_when_one_task_throws_exception(context_obj):
    task_1 = Mock(__name__="task_1", return_value=False)
    task_2 = Mock(__name__="task_2", side_effect=Exception("Boom!"))
    task_3 = Mock(__name__="task_3", return_value=False)
    henrulle(context_obj, [task_1, task_2, task_3], attempts=1)
    all([task_1.called, task_2.called, task_3.called]) | should.be.true


def test_henrulle_must_attempt_sequence_specified_number_of_times(context_obj):
    task_1 = Mock(__name__="task_1", return_value=False)
    task_2 = Mock(__name__="task_2", return_value=False)
    henrulle(context_obj, [task_1, task_2], attempts=3)
    all([task_1.call_count == 3, task_2.call_count == 3]) | should.be.true


def test_henrulle_must_allow_any_task_to_abort_job(context_obj):
    def abort_job():
        context_obj.completed = True
    task_1 = Mock(__name__="task_1", return_value=False)
    task_2 = Mock(__name__="task_2", side_effect=abort_job)
    task_3 = Mock(__name__="task_3", return_value=True)
    henrulle(context_obj, [task_1, task_2, task_3], attempts=1)
    all([task_1.called, task_2.called]) | should.be.true
    task_3.called | should.be.false


def test_henrulle_must_stop_mutiple_attempt_job_when_first_task_succeeds_on_second_try(context_obj):
    task_1 = Mock(__name__="task_1", side_effect=[False, True])
    task_2 = Mock(__name__="task_2", return_value=False)
    henrulle(context_obj, [task_1, task_2], attempts=2)
    task_1.call_count | should.be.equal.to(2)
    task_2.call_count | should.be.equal.to(1)


def test_henrulle_must_enforce_global_timeout(context_obj):
    task_1 = Mock(__name__="task_1", side_effect=lambda: time.sleep(5))
    task_2 = Mock(__name__="task_2", return_value=True)
    context_obj.global_timeout = 0.1
    start_time = time.time()
    henrulle(context_obj, [task_1, task_2], attempts=1)
    time_lapsed = time.time() - start_time
    all([task_1.call_count == 1, task_2.call_count == 1, time_lapsed < 0.3]) | should.be.true


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
    all([task_2_1, task_2_2]) | should.be.true
