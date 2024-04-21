from application.extensions import CELERY


@CELERY.task(bind=True)
def start_agent_monitor(self):
    self.update_state(state="SUCCESS")
    return {"status": "Task Completed!"}
