from celery_worker import app
from celery.exceptions import SoftTimeLimitExceeded
import time

@app.task()
def short():
    time.sleep(1)
    return

@app.task()
def long():
    try:
        time.sleep(60)  # Simulate a long-running task
    except SoftTimeLimitExceeded:
        print("Soft time limit exceeded")
    return

