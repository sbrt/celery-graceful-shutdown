#!/usr/bin/env bash

# How to handle the SIGTERM signal
function terminate_handler() {
    echo "Caught SIGTERM signal!"

    echo "Terminating main process with PID $1"
    kill -TERM "$1"
    echo "Graceful shutdown initiated. Sleeping after process termination."
}

# Start the main process in the background
celery -A celery_worker worker --max-tasks-per-child=10 --loglevel=debug --autoscale=10,10 --prefetch-multiplier=10 &
#celery -A celery_worker worker --max-tasks-per-child=10 --loglevel=debug --concurrency=1 --pool=solo --prefetch-multiplier=10 &

# Store the PID of the celery worker
pid=$!

# Register the terminate_handler function to be called on SIGTERM
trap "terminate_handler '${pid}'" SIGTERM

# Wait for the celery process to exit
wait $pid
# Store the exit code of the celery process
error_code=$?

# Second wait is necessary for celery worker to finish tasks and to return prefetched tasks to the broker
wait

# A return code of 143 means the process was terminated by a SIGTERM signal.
echo "main process exited with $error_code"
