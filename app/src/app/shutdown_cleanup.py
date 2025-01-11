import os
import tempfile
import glob
import json
import random


def update_job_files(base_path):
    for file_path in glob.glob(f"{base_path}/**/job.json", recursive=True):
        with open(file_path, "r") as f:
            job_data = json.load(f)

            if job_data.get("status") in ["PENDING", "RUNNING"]:
                job_data["status"] = "SHUTDOWN"

                with open(file_path, "w") as f:
                    json.dump(job_data, f)

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as base_path:
        statuses = ["PENDING", "RUNNING"]
        for user_id in range(5000):
            for task_id in range(5):
                task_path = os.path.join(base_path, str(user_id), str(task_id))
                os.makedirs(task_path, exist_ok=True)
                job_file = os.path.join(task_path, "job.json")
                with open(job_file, "w") as f:
                    json.dump({"status": random.choice(statuses)}, f)
        update_job_files(base_path=base_path)

        for file_path in glob.glob(f"{base_path}/**/job.json", recursive=True):
            with open(file_path, "r") as f:
                data = json.load(f)
                assert data.get("status") not in ["PENDING", "RUNNING"]
