import subprocess
import requests
import pytest

from typing import Optional
from tenacity import retry, wait_fixed, stop_after_delay, retry_if_exception_type

import json
import redis
import time

# Connect to Redis server
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
REDIS_CONTAINER_NAME = "redis"
TASK_API_URL = "http://localhost:8000/start-task/short"

def up_docker_compose(service: Optional[str] = None, build = False, clean = True):
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

def celery_broker_queue_size(broker = "redis"):
    """Get redis queue length for celery."""
    command = ["docker", "exec", REDIS_CONTAINER_NAME, "redis-cli", "LLEN",  "celery"]
    result = subprocess.run(command, capture_output=True, text=True)
    return int(result.stdout.strip())

def get_task_result(task_id: str) -> dict:
    # The task_id whose result you want to fetch
    key = f'celery-task-meta-{task_id}'

    # Fetch the value of the key from Redis
    task_result = redis_client.get(key)

    # If the key exists, deserialize and convert to a dictionary
    if task_result:
        # Decode from bytes to a string and then parse JSON to dictionary
        task_result_dict = json.loads(task_result.decode('utf-8'))
        return task_result_dict
    return {"status": "PENDING"}

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_module():
    """Setup and teardown for the test."""
    try:
        up_docker_compose(build=True, clean=True)
        yield
    finally:
        down_docker_compose(remove_volumes=True)
        pass


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for the test."""
    try:
        up_docker_compose("redis", clean=True)
        yield
    finally:
        down_docker_compose("redis", remove_volumes=True)
        pass

@retry(
    stop=stop_after_delay(300),        # Stop after 5 minutes
    wait=wait_fixed(5),                # Wait 5 seconds between retries
    retry=retry_if_exception_type(requests.exceptions.ConnectionError)  # Retry only on ConnectionError
)
def submit_test_task():
    response = requests.get(TASK_API_URL)
    print(response.json())
    assert response.status_code == 202, "Task submission failed:" + response.reason
    return response.json()["task_id"]


@pytest.mark.parametrize("ntasks", [100])
def test_celery_tasks(ntasks: int):
    print()

    # Submit tasks
    task_ids = []
    for _ in range(ntasks):
        task_ids.append(submit_test_task())

    # Wait for some tasks to be fetched by the worker
    time.sleep(5)

    # Stop celery worker
    result = stop_docker_compose(service="celery_worker")
    result = subprocess.run(["docker", "compose", "logs", "celery_worker"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

    # Check that all tasks where returned to the broker or succeeded during graceful shutdown
    n_queue_size = celery_broker_queue_size()
    states = [get_task_result(task_id)["status"] for task_id in task_ids]
    n_successful = sum([state == "SUCCESS" for state in states])
    print("Number of tasks: ", ntasks)
    print("Queue size: ", n_queue_size)
    print("Successful: ", n_successful)
    assert n_queue_size + n_successful == ntasks, "Graceful shutdown failed"
