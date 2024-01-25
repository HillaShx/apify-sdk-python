from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from collections import defaultdict
from enum import Enum
from logging import getLogger
from typing import Any, Callable, Coroutine, Union

from pyee.asyncio import AsyncIOEventEmitter

from apify.log import ActorLogFormatter

logger = getLogger(__name__)

########################################################################################################################
# Types


class Event(Enum):
    PERSIST_STATE = 'persistState'
    SYSTEM_INFO = 'systemInfo'
    MIGRATING = 'migrating'
    ABORTING = 'aborting'
    EXIT = 'exit'


Listener = Union[
    Callable[[], None],
    Callable[[Any], None],
    Callable[[], Coroutine[Any, Any, None]],
    Callable[[Any], Coroutine[Any, Any, None]],
]

########################################################################################################################
# EventManager
#   - Minimal version, without platform interaction


class EventManager:
    """A class for managing events."""

    def __init__(self: EventManager) -> None:
        self._event_emitter = AsyncIOEventEmitter()
        self._listener_tasks: set[asyncio.Task] = set()
        self._listeners_to_wrappers: dict[str, dict[Callable, list[Callable]]] = defaultdict(lambda: defaultdict(list))

    async def close(self: EventManager, event_listeners_timeout_secs: float | None = None) -> None:
        await self.wait_for_all_listeners_to_complete(timeout_secs=event_listeners_timeout_secs)
        self._event_emitter.remove_all_listeners()

    def on(self: EventManager, event: Event, listener: Listener) -> Callable:
        # Detect whether the listener will accept the event_data argument
        try:
            signature = inspect.signature(listener)
        except (ValueError, TypeError):
            # If we can't determine the listener argument count (e.g. for the built-in `print` function),
            # let's assume the listener will accept the argument
            listener_argument_count = 1
        else:
            try:
                dummy_event_data: dict = {}
                signature.bind(dummy_event_data)
                listener_argument_count = 1
            except TypeError:
                try:
                    signature.bind()
                    listener_argument_count = 0
                except TypeError as err:
                    raise ValueError('The "listener" argument must be a callable which accepts 0 or 1 arguments!') from err

        event_name = event.value

        async def inner_wrapper(event_data: Any) -> None:
            if inspect.iscoroutinefunction(listener):
                if listener_argument_count == 0:
                    await listener()
                else:
                    await listener(event_data)
            elif listener_argument_count == 0:
                listener()  # type: ignore[call-arg]
            else:
                listener(event_data)  # type: ignore[call-arg]

        async def outer_wrapper(event_data: Any) -> None:
            listener_task = asyncio.create_task(inner_wrapper(event_data))
            self._listener_tasks.add(listener_task)
            try:
                await listener_task
            except asyncio.CancelledError:
                raise
            except Exception:
                # We need to swallow the exception and just log it here, since it could break the event emitter otherwise
                logger.exception('Exception in event listener', extra={'event_name': event_name, 'listener_name': listener.__name__})
            finally:
                self._listener_tasks.remove(listener_task)

        self._listeners_to_wrappers[event_name][listener].append(outer_wrapper)

        return self._event_emitter.add_listener(event_name, outer_wrapper)

    def off(self: EventManager, event: Event, listener: Callable | None = None) -> None:
        event_name = event.value

        if listener:
            for listener_wrapper in self._listeners_to_wrappers[event_name][listener]:
                self._event_emitter.remove_listener(event_name, listener_wrapper)
            self._listeners_to_wrappers[event_name][listener] = []
        else:
            self._listeners_to_wrappers[event_name] = defaultdict(list)
            self._event_emitter.remove_all_listeners(event_name)

    def emit(self: EventManager, event: Event, data: Any) -> None:
        event_name = event.value
        self._event_emitter.emit(event_name, data)

    async def wait_for_all_listeners_to_complete(self: EventManager, *, timeout_secs: float | None = None) -> None:
        logger.debug('Waiting for all event listeners to complete...')

        async def _wait_for_listeners() -> None:
            logger.debug('Waiting for all event listeners to complete -> inner...')

            logger.debug(f'self._listener_tasks (len={len(self._listener_tasks)}) = {self._listener_tasks}')
            logger.debug(f'asyncio.all_tasks (len={len(asyncio.all_tasks())}) = {asyncio.all_tasks()}')

            results = await asyncio.gather(*self._listener_tasks, return_exceptions=True)
            for result in results:
                if result is Exception:
                    logger.exception('Event manager encountered an exception in one of the event listeners', exc_info=result)

        if timeout_secs:
            _, pending = await asyncio.wait([asyncio.create_task(_wait_for_listeners())], timeout=None)
            if pending:
                logger.warning('Timed out waiting for event listeners to complete, unfinished event listeners will be canceled')
                for pending_task in pending:
                    pending_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await pending_task
        else:
            # Bug:
            await _wait_for_listeners()

            # Possible solution:
            # await asyncio.gather(asyncio.create_task(_wait_for_listeners()))
            # or asyncio.wait


########################################################################################################################
# Run

# Configuration of the root logger
handler = logging.StreamHandler()
handler.setFormatter(ActorLogFormatter(include_logger_name=True))
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)


async def async_handler_01(*args: Any, **kwargs: Any) -> None:
    print('Starting async_handler_01...')
    await asyncio.sleep(0.1)
    print(f'args={args}, kwargs={kwargs}')
    await asyncio.sleep(0.1)
    print('Finishing async_handler_01...')


async def main() -> None:
    logger.info('Starting the main...')

    event_manager = EventManager()
    event_manager.on(event=Event.PERSIST_STATE, listener=async_handler_01)
    event_manager.emit(event=Event.PERSIST_STATE, data={'data': 123, 'more_data': 'abc'})

    logger.info('Waiting for all listeners to complete...')
    await event_manager.wait_for_all_listeners_to_complete()
    logger.info('Done waiting for all listeners to complete.')


if __name__ == '__main__':
    asyncio.run(main())
