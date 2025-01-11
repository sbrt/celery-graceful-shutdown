import subprocess
import requests
import time
import pytest

from collections import Counter
from tabulate import tabulate
from celery import Celery
from typing import Optional

# Configure Celery client (modify as needed for your setup)
REDIS_CONTAINER_NAME = "redis"
REDIS_BACKEND = "redis://localhost:6379//0"

celery_app = Celery("tasks", broker=REDIS_BACKEND, backend=REDIS_BACKEND)


API_URL = "http://localhost:8000/start-task/short"
WAIT_TIME = 2  # Time (in seconds) to wait between task status checks
MAX_RETRIES = 10  # Maximum number of retries to check the status

def up_docker_compose(service: Optional[str] = None, build = True, clean = False):
    """Start the deployment using Docker Compose."""
    command = ["docker", "compose", "up", "-d"] + ([service] if service else []) + (["--build"] if build else []) + (["--renew-anon-volumes", "--force-recreate"] if clean else [])
    return subprocess.run(command, check=True, capture_output=True, text=True)

def down_docker_compose(service: Optional[str] = None, remove_volumes = False):
    """Stop the deployment using Docker Compose."""
    command = ["docker", "compose", "down"] + ([service] if service else []) + (["--volumes"] if remove_volumes else [])
    return subprocess.run(command, check=True, capture_output=True, text=True)

def stop_docker_compose(service: str):
    """Stop the deployment using Docker Compose."""
    command = ["docker", "compose", "stop", service]
    return subprocess.run(command, check=True, capture_output=True, text=True)

def check_task_status(task_id):
    """Check the status of a task using Celery's result backend."""
    result = celery_app.AsyncResult(task_id, app=celery_app)
    return result.state

def celery_broker_queue_size(broker = "redis"):
    """Get redis queue length for celery."""
    command = ["docker", "exec", REDIS_CONTAINER_NAME, "redis-cli", "LLEN",  "celery"]
    result = subprocess.run(command, capture_output=True, text=True)
    return int(result.stdout.strip())

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Setup and teardown for the test."""
    try:
        #stop_docker_compose(remove_volumes=True)
        #start_docker_compose(clean=True)
        #time.sleep(20)  # Allow time for services to start
        yield
    finally:
        #stop_docker_compose(remove_volumes=True)
        pass

@pytest.mark.parametrize("ntasks", [5, 50, 500])
def test_celery_tasks(ntasks: int):
    task_ids = []

    # Submit tasks
    for _ in range(ntasks):
        response = requests.get(API_URL)
        assert response.status_code == 202, "Task submission failed:" + response.reason
        print(response.json())
        task_ids.append(response.json()["task_id"])

    # Stop celery worker
    result = stop_docker_compose(service="celery_worker")
    result = subprocess.run(["docker", "compose", "logs", "celery_worker"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    #time.sleep(70)
    # Check that all tasks where returned to the broker or succeeded during graceful shutdown
    n_queue_size = celery_broker_queue_size()
    states = [check_task_status(task_id) for task_id in task_ids]
    n_successful = sum([state == "SUCCESS" for state in states])
    print(dict(zip(task_ids, states)))
    print(dict(zip(task_ids, [celery_app.AsyncResult(task_id).result for task_id in task_ids])))
    print("Queue size: ", n_queue_size)
    print("Successful: ", n_successful)

    frequency = Counter()

    # Prepare data for the table (converting Counter to a list of tuples)
    table_data = [(item, count) for item, count in frequency.items()]

    # Define the table headers
    headers = ["Item", "Frequency"]

    # Print the table
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    assert n_queue_size + n_successful == ntasks, "Graceful shutdown failed"
