from application.common import logger
from application.extensions import CELERY


# Revoke a task by id directly.
def revoke_task_by_id(task_id: str) -> bool:
    CELERY.control.revoke(task_id, terminate=True)


# A function to revoke a task from the Celery queue using monitor_id and task_name as input.
def revoke_task(task_name: str, monitor_id: int, is_scheduled=False) -> bool:
    """
    Revoke a task from the Celery queue.

    Args:
        task_name: The name of the task to revoke.
        monitor_id: The monitor_id to revoke the task for.
    """

    revoked = False

    if is_scheduled:
        scheduled_tasks = CELERY.control.inspect().scheduled()
        for _, scheduled_task in scheduled_tasks.items():
            for task in scheduled_task:
                request = task["request"]
                args = request["args"]  # only ever has one arg
                if request["name"] == task_name and args[0] == monitor_id:
                    task_id = task["request"]["id"]
                    logger.debug(f"Revoking scheduled task {task_name} with task_id {task_id}")
                    CELERY.control.revoke(task_id, terminate=True)
                    revoked = True
                    break
    else:
        active_tasks = CELERY.control.inspect().active()
        for _, active_task in active_tasks.items():
            for task in active_task:
                args = task["args"]  # only ever has one arg
                if task["name"] == task_name and args[0] == monitor_id:
                    task_id = task["id"]
                    logger.debug(f"Revoking active task {task_name} with task_id {task_id}")
                    CELERY.control.revoke(task_id, terminate=True)
                    revoked = True
                    break

    return revoked


def is_task_scheduled(task_name: str, monitor_id: int) -> bool:
    """
    Check if a task is already scheduled in the Celery queue.

    Args:
        task_name: The name of the task to check.
        monitor_id: The monitor_id to check for.
    """
    scheduled_tasks = CELERY.control.inspect().scheduled()
    for _, scheduled_task in scheduled_tasks.items():
        for task in scheduled_task:
            request = task["request"]
            args = request["args"]  # only ever has one arg
            if request["name"] == task_name and args[0] == monitor_id:
                return True

    return False


def is_task_running(task_name: str, monitor_id: int) -> bool:
    """
    Check if a task is already running in the Celery queue.

    Args:
        task_name: The name of the task to check.
        monitor_id: The monitor_id to check for.
    """
    active_tasks = CELERY.control.inspect().active()
    for _, active_task in active_tasks.items():
        for task in active_task:
            args = task["args"]  # only ever has one arg
            if task["name"] == task_name and args[0] == monitor_id:
                return True

    return False
