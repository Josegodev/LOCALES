import asyncio
import contextlib
import inspect
import sys
import threading
from concurrent.futures import Future
from importlib.metadata import PackageNotFoundError, version

import anyio.from_thread


class _CompatTaskStatus:
    def __init__(self, event: threading.Event, box: dict[str, object]) -> None:
        self._event = event
        self._box = box

    def started(self, value: object = None) -> None:
        self._box["value"] = value
        self._event.set()


class _CompatBlockingPortal:
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def call(self, func, *args):
        done = threading.Event()
        box: dict[str, object] = {}

        async def runner() -> None:
            try:
                result = func(*args)
                if inspect.isawaitable(result):
                    result = await result
            except BaseException as exc:
                box["exc"] = exc
            else:
                box["result"] = result
            finally:
                done.set()

        self._loop.call_soon_threadsafe(lambda: self._loop.create_task(runner()))
        if not done.wait(5):
            raise TimeoutError("Compat blocking portal call timed out")
        if "exc" in box:
            raise box["exc"]
        return box.get("result")

    def start_task_soon(self, func, *args, name=None) -> Future:
        future: Future = Future()
        task_box: dict[str, asyncio.Task[object]] = {}

        async def runner() -> None:
            try:
                result = func(*args)
                if inspect.isawaitable(result):
                    result = await result
            except asyncio.CancelledError:
                future.cancel()
            except BaseException as exc:
                future.set_exception(exc)
            else:
                future.set_result(result)

        def schedule() -> None:
            task = self._loop.create_task(
                runner(), name=str(name) if name is not None else None
            )
            task_box["task"] = task

        self._loop.call_soon_threadsafe(schedule)

        def propagate_cancel(done_future: Future) -> None:
            task = task_box.get("task")
            if done_future.cancelled() and task is not None:
                self._loop.call_soon_threadsafe(task.cancel)

        future.add_done_callback(propagate_cancel)
        return future

    def start_task(self, func, *args, name=None):
        future: Future = Future()
        started_event = threading.Event()
        started_box: dict[str, object] = {}
        task_box: dict[str, asyncio.Task[object]] = {}

        async def runner() -> None:
            try:
                task_status = _CompatTaskStatus(started_event, started_box)
                result = func(*args, task_status=task_status)
                if inspect.isawaitable(result):
                    result = await result
                if not started_event.is_set():
                    started_event.set()
            except asyncio.CancelledError:
                if not started_event.is_set():
                    started_event.set()
                future.cancel()
            except BaseException as exc:
                if not started_event.is_set():
                    started_event.set()
                future.set_exception(exc)
            else:
                future.set_result(result)

        def schedule() -> None:
            task = self._loop.create_task(
                runner(), name=str(name) if name is not None else None
            )
            task_box["task"] = task

        self._loop.call_soon_threadsafe(schedule)
        started_event.wait(timeout=2)

        def propagate_cancel(done_future: Future) -> None:
            task = task_box.get("task")
            if done_future.cancelled() and task is not None:
                self._loop.call_soon_threadsafe(task.cancel)

        future.add_done_callback(propagate_cancel)
        return future, started_box.get("value")


@contextlib.contextmanager
def _compat_start_blocking_portal(backend: str = "asyncio", backend_options=None):
    if backend != "asyncio":
        raise RuntimeError(f"Unsupported backend for compat portal: {backend}")

    loop = asyncio.new_event_loop()

    def run_loop() -> None:
        asyncio.set_event_loop(loop)

        def tick() -> None:
            if loop.is_closed():
                return
            loop.call_later(0.01, tick)

        loop.call_soon(tick)
        loop.run_forever()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
        loop.close()

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    try:
        yield _CompatBlockingPortal(loop)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)


def _should_patch_blocking_portal() -> bool:
    if sys.version_info[:2] != (3, 12):
        return False
    try:
        anyio_version = version("anyio")
    except PackageNotFoundError:
        return False
    return anyio_version == "4.13.0"


def apply_blocking_portal_compat_patch() -> None:
    if not _should_patch_blocking_portal():
        return
    if (
        getattr(anyio.from_thread.start_blocking_portal, "__name__", "")
        == "_compat_start_blocking_portal"
    ):
        return
    anyio.from_thread.start_blocking_portal = _compat_start_blocking_portal
