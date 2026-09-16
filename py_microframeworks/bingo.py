import threading
import time
from typing import Callable, Dict, List


class Bingo:  # pylint: disable=too-many-instance-attributes,too-many-positional-arguments
    """Add cells. When conditions for cells match, they fire. By default cells get used up.
    """
    def __init__(self, state: Dict, pulse_function: Callable, max_iterations: int = 5,
                 log_delegate=print, consecutive: bool = False):  # pylint: disable=too-many-arguments
        self.state = state
        self.cells: List[Dict] = []
        self.pulse_function = pulse_function
        self.running = False
        self.thread = None
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.log_delegate = log_delegate
        self.start_time = 0
        self.consecutive = consecutive
        self.complete = False

    def add_cell(self, *expressions, callback=None, callback_msg=None, use_up=True):
        assert not (self.consecutive and not use_up), \
            "The use_up property must always be True when running in consecutive mode"
        self.cells.append({
            "expressions": expressions,
            "callback": callback,
            "triggered": False,
            "callback_msg": callback_msg,
            "use_up": use_up,
            "executed": False
        })

    def run(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.start_time = time.monotonic()
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join()

    def wait(self, poll: float = 1):
        self.run()
        while self.running and self.current_iteration < self.max_iterations \
            and any(self._remaining_cells()):
            time.sleep(poll)
        if self.thread:
            self.thread.join()
        remaining_cells = [cell for cell in self.cells if not cell["executed"]]
        self.log_delegate((f"Bingo finished in {time.monotonic() - self.start_time}s. "
                           f"Total iterations: {self.current_iteration}. "
                           f"Number of unexecuted cells: {len(remaining_cells)}"))
        self.complete = len(remaining_cells) == 0

    def _remaining_cells(self):
        for cell in self.cells:
            if not cell["triggered"]:
                yield cell

    def _execute_expr(self, expr):
        if isinstance(expr, str):
            return eval(expr, {}, self.state)  # pylint: disable=W0123
        if callable(expr):
            return expr()
        raise TypeError(f"Expression must be a str or callable, got {type(expr).__name__}")

    def _has_uncalled_priors(self, index):
        return not all(cell["triggered"] for cell in self.cells[:index])

    def _fire_cell(self, cell):
        if cell["callback"]:
            cell["callback"]()
        cell["triggered"] = cell["use_up"]
        if cell["callback_msg"]:
            self.log_delegate(cell["callback_msg"])
        cell["executed"] = True

    def _monitor(self):
        while (
            self.running
            and self.current_iteration < self.max_iterations
            and any(self._remaining_cells())
        ):
            for index, cell in enumerate(self.cells):
                if not cell["triggered"]:
                    if self.consecutive and self._has_uncalled_priors(index):
                        continue
                    try:
                        if all(self._execute_expr(expr) for expr in cell["expressions"]):
                            self._fire_cell(cell)
                    except Exception as ex:  # pylint: disable=W0718
                        self.log_delegate("Failed to evaluate expressions: "
                                          f"{cell['expressions']}. Got exception\n{ex}")
            self.current_iteration += 1
            self.state["remaining_iterations"] = self.max_iterations - self.current_iteration
            self.pulse_function()
        self.running = False
