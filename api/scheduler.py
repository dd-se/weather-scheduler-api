from collections.abc import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from .logging import get_logger

logger = get_logger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown()


def add_job(job_id: int, interval_hours: float, callback: Callable[..., None], *args) -> None:
    scheduler.add_job(callback, "interval", seconds=int(interval_hours * 3600), id=str(job_id), args=args)
    logger.info(f"Scheduled '{callback.__name__}' for job ID '{job_id}' with interval '{interval_hours}' hour(s)")


def remove_job(job_id: int):
    try:
        scheduler.remove_job(str(job_id))
        logger.info(f"Removed scheduled job ID '{job_id}'")
    except Exception:
        pass


def update_job_interval(job_id: int, interval_hours: float, callback: Callable[..., None], *args):
    logger.info(f"Updating interval for job ID '{job_id}'")
    remove_job(job_id)
    add_job(job_id, interval_hours, callback, args)
