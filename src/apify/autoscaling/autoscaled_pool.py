"""
Inspiration:
https://github.com/apify/crawlee/blob/master/packages/core/src/autoscaling/autoscaled_pool.ts
"""


from logging import Logger
from typing import Coroutine, Optional


class AutoscaledPool:
    """
    Todo
    """

    def __init__(
        self,
        run_task_function: Coroutine,
        is_task_ready_function: Coroutine,
        is_finished_function: Coroutine,
        min_concurrency: int = 1,
        max_concurrency: int = 200,
        desired_concurrency: Optional[int] = None,
        desired_concurrency_ratio: float = 0.9,
        scale_up_step_ratio: float = 0.05,
        scale_down_step_ratio: float = 0.05,
        maybe_run_interval_secs: float = 0.5,
        logging_interval_secs: Optional[float] = 60,
        autoscale_interval_secs: float = 10,
        task_timeout_secs: float = 0,
        max_tasks_per_minute: float = float('inf'),
        log: Optional[Logger] = None,
    ) -> None:
        # Configurable properties
        self.run_task_function = run_task_function
        self.is_task_ready_function = is_task_ready_function
        self.is_finished_function = is_finished_function
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.desired_concurrency = desired_concurrency
        self.desired_concurrency_ratio = desired_concurrency_ratio
        self.scale_up_step_ratio = scale_up_step_ratio
        self.scale_down_step_ratio = scale_down_step_ratio
        self.maybe_run_interval_secs = maybe_run_interval_secs
        self.logging_interval_secs = logging_interval_secs
        self.autoscale_interval_secs = autoscale_interval_secs
        self.task_timeout_secs = task_timeout_secs
        self.max_tasks_per_minute = max_tasks_per_minute
        self.log = log
        # Todo: Snapshotter Options
        # Todo: SystemStatus Options

        self.current_concurrency = 0

    def abort(self) -> None:
        pass

    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def run(self) -> None:
        pass

#
