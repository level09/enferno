"""Async background tasks and scheduled jobs.

Usage:
    # Fire-and-forget background task
    from enferno.tasks import run_in_background

    async def my_handler():
        await run_in_background(send_welcome_email(user_id=123))

    # Scheduled/cron jobs (uncomment APScheduler setup in app.py)
    # See schedule_jobs() below for examples
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_in_background(coro):
    """Fire-and-forget async task with error logging.

    Use for work that doesn't need a result: emails, webhooks, cache warming, etc.
    The task runs in the current event loop — no extra processes, no Redis.
    """
    task = asyncio.create_task(coro)
    task.add_done_callback(_log_task_exception)
    return task


async def run_with_session(coro_factory):
    """Fire-and-forget async task that gets its own DB session.

    coro_factory is an async callable that takes a session argument:
        async def my_task(session):
            await session.execute(...)

        await run_with_session(my_task)
    """
    import enferno.extensions as ext

    async def _wrapper():
        async with ext.async_session_factory() as session:
            try:
                await coro_factory(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return await run_in_background(_wrapper())


def _log_task_exception(task: asyncio.Task):
    if not task.cancelled() and task.exception():
        logger.error(
            "Background task failed: %s", task.exception(), exc_info=task.exception()
        )


async def cleanup_expired_sessions():
    """Deactivate expired sessions and delete very old rows."""
    from datetime import datetime, timedelta

    import enferno.extensions as ext
    from enferno.user.models import Session

    async with ext.async_session_factory() as session:
        lifetime = 3600  # default PERMANENT_SESSION_LIFETIME
        cutoff = datetime.now() - timedelta(seconds=lifetime)
        delete_cutoff = datetime.now() - timedelta(days=30)

        # Deactivate expired
        from sqlalchemy import delete as sa_delete
        from sqlalchemy import update

        await session.execute(
            update(Session)
            .where(Session.is_active == True, Session.created_at < cutoff)  # noqa: E712
            .values(is_active=False)
        )
        # Delete old rows
        await session.execute(
            sa_delete(Session).where(Session.created_at < delete_cutoff)
        )
        await session.commit()
        logger.info("Session cleanup complete")


# --- Scheduled Jobs (APScheduler) ---
# To enable: `uv pip install apscheduler` and uncomment setup_scheduler() in app.py
#
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# scheduler = AsyncIOScheduler()
#
# def setup_scheduler(app):
#     """Call from app.py register_extensions() to start scheduled jobs."""
#
#     async def example_cleanup():
#         """Runs daily — clean up expired sessions, old activity logs, etc."""
#         async with app.app_context():
#             # your cleanup logic here
#             pass
#
#     scheduler.add_job(example_cleanup, "cron", hour=3, minute=0, id="daily_cleanup")
#     scheduler.start()
