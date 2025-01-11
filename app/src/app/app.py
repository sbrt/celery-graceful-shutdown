import signal

from signal_handler import chain_signal_handler_to_previous
from flask import Flask, jsonify
from celery import signature, Celery
from celery.canvas import Signature

app = Flask(__name__)

    #broker="pyamqp://user:password@rabbitmq//",
celery_app = Celery(
    "app",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

def my_signal_handler(signum, frame):
    print("Custom handler called for signal:", signum)

# does interrupt in terminal
chain_signal_handler_to_previous(signal.SIGINT, my_signal_handler)
chain_signal_handler_to_previous(signal.SIGTERM, my_signal_handler)

@app.route('/start-task/<task_type>', methods=['GET'])
def start_task(task_type):
    print(task_type)
    if task_type == "short":
        task_signature = signature('tasks.short')
    elif task_type == "long":
        task_signature = signature('tasks.long')
    else:
        return jsonify({"error": "Invalid task type"}), 400
    assert isinstance(task_signature, Signature)
    task = task_signature.apply_async()
    return jsonify({"task_id": task.id}), 202

@app.route('/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id)
    res = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result,
    }
    print(res)
    return jsonify(res)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
