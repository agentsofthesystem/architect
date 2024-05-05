from datetime import datetime

from application.common import logger, constants
from application.extensions import CELERY
from application.workers import monitor_utils


@CELERY.task(bind=True)
def test_task(self, monitor_id: int):
    logger.debug(f"Agent Health TEST Task Running at {datetime.now()}")

    monitor_obj = monitor_utils._get_monitor_obj(monitor_id)

    if monitor_obj is None:
        logger.error(f"Monitor ID {monitor_id} not found.")
        return {"status": "Monitor ID not found."}

    next_interval = constants.DEFAULT_MONITOR_TESTING_INTERVAL

    if monitor_obj.active:
        logger.debug(f"Monitor ID {monitor_id} is active. Scheduling next health check.")
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id)
        self.apply_async(
            [monitor_id],
            countdown=next_interval,
        )
    else:
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id, is_stopped=True)
        logger.debug(f"Monitor ID {monitor_id} is not active. Stopping further health checks..")
