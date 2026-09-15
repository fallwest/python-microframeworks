from contextlib import suppress
from typing import Callable, List

import timeout_timer


def henrulle(context, tasks: List[Callable], attempts: int = 2, custom_log_delegate=None, signal="completed") -> None:
    """Execute a list of tasks until one of them returns True, or all attempts are exhausted.

    Args:
        context (NeatContext): A context object with a boolean completed flag that indicates whether
        the job is complete. Set the completed flag to True to terminate the job.
        tasks (List[Callable]): A list of callables that return a boolean indicating whether the task is complete.
        attempts (int, optional): The number of times to attempt the task sequence before giving up. Defaults to 2.
        signal (string, optional): The name of the property on the context object to use as a completed flag.
    """
    with IndentLevel() as indent_level_mgr:
        index = -1
        setattr(context, "index", index)
        completed_signal = getattr(context, signal) if hasattr(context, signal) else False
        setattr(context, signal, completed_signal)
        for _ in range(attempts):
            if getattr(context, signal):
                return
            for task in tasks:
                index += 1
                setattr(context, "index", index)
                is_completed = None
                indent = " " * 4 if indent_level_mgr.indent_level > 0 else ""
                task_name = f"{task.__name__} ({index})"
                with suppress(Exception):
                    if hasattr(context, "global_timeout"):
                        try:
                            with timeout_timer.timeout(context.global_timeout) as gt:
                                is_completed = gt(task)
                        except timeout_timer.TimeoutInterrupt:
                            pass
                    else:
                        is_completed = task()
                msg = f"{task_name}: {is_completed}"
                if custom_log_delegate:
                    custom_log_delegate(indent + msg)
                if is_completed:
                    setattr(context, signal, True)
                # Exit if completed by task, or job terminated by setting `completed` flag somewhere else
                if getattr(context, signal):
                    return


# Source - https://stackoverflow.com/a/44805246
# Posted by Billy, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-20, License - CC BY-SA 3.0

class IndentLevel:
    indent_level = -1

    def __enter__(self):
        self.adjust_indent_level(1)
        return self

    def __exit__(self, *a, **k):
        self.adjust_indent_level(-1)

    @classmethod
    def adjust_indent_level(cls, val):
        cls.indent_level += val
