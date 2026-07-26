"""Per-thread asyncio event loop for the frozen ragtime package.

ragtime's text_generator drives litellm with
``asyncio.get_event_loop().run_until_complete(...)``, which requires the
calling thread to already own an event loop. The main thread gets one
implicitly, but none of our generation code runs there: jobs run in the
runner's ThreadPoolExecutor and the generation endpoints run in gunicorn's
gthread worker threads — where ``get_event_loop()`` raises
``RuntimeError: There is no current event loop in thread ...``.

``ensure_event_loop()`` gives the current thread a persistent loop on first
use. Pool threads are long-lived and reused, so each thread pays this once
and the package then finds its loop as designed. Call it immediately before
any ``*.generate(...)`` / evaluation call into the package.
"""
import asyncio


def ensure_event_loop():
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
