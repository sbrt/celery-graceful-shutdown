from celery import Celery, signals, result


#broker="pyamqp://user:password@rabbitmq//",
app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

app.conf.update(
    task_track_started = True,
    # acknowledge tasks after they are done, in case of power failture
    # with redis queue with AOF persistence, tasks will be re-executed even in case of power failure
    #task_acks_late = True,
    # requeue task on power failure
    #task_reject_on_worker_lost=False,
    # prevent multiple additions of the same task with task_acks_late
    # and enforce time limit on jobs
    #task_time_limit = 120,
    #task_soft_time_limit = 120 - 10,
)
# adapt to task time limit
#app.conf.broker_transport_options = {'visibility_timeout': 120 + 10}

#app.autodiscover_tasks(['tasks'])
import tasks

if __name__ == "__main__":
    app.start()
