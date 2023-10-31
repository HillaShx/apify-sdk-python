"""
Inspiration:
https://github.com/apify/crawlee/blob/master/packages/core/src/autoscaling/snapshotter.ts
"""

from dataclasses import dataclass, field
from datetime import datetime
from logging import Logger

from typing import Optional

from ..config import Configuration
from .._memory_storage.resource_clients import BaseResourceClient

RESERVE_MEMORY_RATIO = 0.5
CLIENT_RATE_LIMIT_ERROR_RETRY_COUNT = 2
CRITICAL_OVERLOAD_RATE_LIMIT_MILLIS = 10000


# @dataclass
# class SnapshotterOptions:
#     event_loop_snapshot_interval_secs: float = 0.5
#     client_snapshot_interval_secs: float = 1
#     max_blocked_millis: int = 50
#     max_used_memory_ratio: float = 0.7
#     max_client_errors: int = 1
#     snapshot_history_secs: int = 60
#     log: Optional[Logger] = None
#     client: Optional[BaseResourceClient] = None
#     config: Optional[Configuration] = None


@dataclass
class MemorySnapshot:
    created_at: datetime
    is_overloaded: bool
    used_bytes: Optional[int]


@dataclass
class CpuSnapshot:
    created_at: datetime
    is_overloaded: bool
    used_ratio: float
    ticks_idle: Optional[float]
    ticks_total: Optional[float]


@dataclass
class EventLoopSnapshot:
    created_at: datetime
    is_overloaded: bool
    exceeded_millis: float


@dataclass
class ClientSnapshot:
    created_at: datetime
    is_overloaded: bool
    rate_limit_error_count: int


class Snapshotter:
    """
    Todo
    """

    def __init__(
        self,
        log: Logger,
        client: BaseResourceClient,
        config: Configuration,
        event_loop_snapshot_interval_secs: float = 0.5,
        client_snapshot_interval_secs: float = 1,
        max_blocked_millis: int = 50,
        max_used_memory_ratio: float = 0.7,
        max_client_errors: int = 1,
        snapshot_history_secs: int = 60,
    ) -> None:
        self.log = log
        self.client = client
        self.config = config
        self.event_loop_snapshot_interval_secs = event_loop_snapshot_interval_secs
        self.client_snapshot_interval_secs = client_snapshot_interval_secs
        self.max_blocked_millis = max_blocked_millis
        self.max_used_memory_ratio = max_used_memory_ratio
        self.max_client_errors = max_client_errors
        self.snapshot_history_secs = snapshot_history_secs

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def get_memory_sample(self) -> None:
        pass

#
