"""
Inspiration:
https://github.com/apify/crawlee/blob/master/packages/core/src/autoscaling/system_status.ts
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import date

from ..config import Configuration


@dataclass
class Snapshotter:
    # This is gonna be imported from other modules
    pass


@dataclass
class ClientInfo:
    is_overloaded: bool
    limit_ratio: float
    actual_ratio: float


@dataclass
class SystemInfo:
    is_system_idle: bool
    mem_info: ClientInfo
    event_loop_info: ClientInfo
    cpu_info: ClientInfo
    client_info: ClientInfo
    mem_current_bytes: Optional[int] = None
    cpu_current_usage: Optional[int] = None
    is_cpu_overloaded: Optional[bool] = None
    created_at: Optional[date] = None


@dataclass
class SystemStatusOptions:
    current_history_secs: Optional[int] = 5
    max_memory_overloaded_ratio: Optional[float] = 0.2
    max_event_loop_overloaded_ratio: Optional[float] = 0.6
    max_cpu_overloaded_ratio: Optional[float] = 0.4
    max_client_overloaded_ratio: Optional[float] = 0.3
    snapshotter: Optional[Snapshotter] = None
    config: Optional[Configuration] = None


@dataclass
class FinalStatistics:
    requests_finished: int
    requests_failed: int
    retry_histogram: List[int]
    request_avg_failed_duration_millis: float
    request_avg_finished_duration_millis: float
    requests_finished_per_minute: float
    requests_failed_per_minute: float
    request_total_duration_millis: float
    requests_total: int
    crawler_runtime_millis: float


class SystemStatus:
    def __init__(self, options: Optional[dict] = None):
        if options is None:
            options = {}

        current_history_secs = options.get('currentHistorySecs', 5)
        max_memory_overloaded_ratio = options.get('maxMemoryOverloadedRatio', 0.2)
        max_event_loop_overloaded_ratio = options.get('maxEventLoopOverloadedRatio', 0.6)
        max_cpu_overloaded_ratio = options.get('maxCpuOverloadedRatio', 0.4)
        max_client_overloaded_ratio = options.get('maxClientOverloadedRatio', 0.3)
        snapshotter = options.get('snapshotter', Snapshotter())
        config = options.get('config', None)

        self.current_history_secs = current_history_secs * 1000
        self.max_memory_overloaded_ratio = max_memory_overloaded_ratio
        self.max_event_loop_overloaded_ratio = max_event_loop_overloaded_ratio
        self.max_cpu_overloaded_ratio = max_cpu_overloaded_ratio
        self.max_client_overloaded_ratio = max_client_overloaded_ratio
        self.snapshotter = snapshotter

    def get_current_status(self) -> SystemInfo:
        return self._is_system_idle(self.current_history_secs)

    def get_historical_status(self) -> SystemInfo:
        return self._is_system_idle()

    def _is_system_idle(self, sample_duration_millis: Optional[int] = None) -> SystemInfo:
        mem_info = self._is_memory_overloaded(sample_duration_millis)
        event_loop_info = self._is_event_loop_overloaded(sample_duration_millis)
        cpu_info = self._is_cpu_overloaded(sample_duration_millis)
        client_info = self._is_client_overloaded(sample_duration_millis)

        return SystemInfo(
            is_system_idle=(not mem_info.is_overloaded and
                            not event_loop_info.is_overloaded and
                            not cpu_info.is_overloaded and
                            not client_info.is_overloaded),
            mem_info=mem_info,
            event_loop_info=event_loop_info,
            cpu_info=cpu_info,
            client_info=client_info
        )

    def _is_memory_overloaded(self, sample_duration_millis: Optional[int] = None) -> ClientInfo:
        sample = self.snapshotter.get_memory_sample(sample_duration_millis)
        return self._is_sample_overloaded(sample, self.max_memory_overloaded_ratio)

    def _is_event_loop_overloaded(self, sample_duration_millis: Optional[int] = None) -> ClientInfo:
        sample = self.snapshotter.get_event_loop_sample(sample_duration_millis)
        return self._is_sample_overloaded(sample, self.max_event_loop_overloaded_ratio)

    def _is_cpu_overloaded(self, sample_duration_millis: Optional[int] = None) -> ClientInfo:
        sample = self.snapshotter.get_cpu_sample(sample_duration_millis)
        return self._is_sample_overloaded(sample, self.max_cpu_overloaded_ratio)

    def _is_client_overloaded(self, sample_duration_millis: Optional[int] = None) -> ClientInfo:
        sample = self.snapshotter.get_client_sample(sample_duration_millis)
        return self._is_sample_overloaded(sample, self.max_client_overloaded_ratio)

    def _is_sample_overloaded(self, sample: List[dict], ratio: float) -> ClientInfo:
        if not sample:
            return ClientInfo(is_overloaded=False, limit_ratio=ratio, actual_ratio=0)

        weights = []
        values = []

        for i in range(1, len(sample)):
            previous = sample[i - 1]
            current = sample[i]
            weight = (current['createdAt'] - previous['createdAt']).total_seconds()
            weights.append(weight or 1)  # Prevent errors from 0 seconds long intervals (sync) between snapshots.
            values.append(current['isOverloaded'])

        w_avg = values[0] if len(sample) == 1 else sum(x * y for x, y in zip(values, weights)) / sum(weights)

        return ClientInfo(
            is_overloaded=w_avg > ratio,
            limit_ratio=ratio,
            actual_ratio=round(w_avg, 3)
        )

#
