from auction.celery import app


def revoke_celery_task(task_id):
    app.control.revoke(task_id=task_id)
