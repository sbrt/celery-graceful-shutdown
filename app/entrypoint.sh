#!/usr/bin/env bash

# How to handle the SIGTERM signal
function terminate_handler() {
    echo "Caught SIGTERM signal!"

    echo "Terminating main process with PID $1"
    kill -TERM "$1"
    echo "Graceful shutdown initiated. Sleeping after process termination."
}
# Start the main process in the background
gunicorn --log-level debug --graceful-timeout 30 --bind 0.0.0.0:8000 app:app &

# Store the PID of the celery worker
pid=$!

# Register the terminate_handler function to be called on SIGTERM
trap "terminate_handler '${pid}'" SIGTERM

# Wait for the celery process to exit
wait $pid
# Store the exit code of the celery process
error_code=$?

wait

# A return code of 143 means the process was terminated by a SIGTERM signal, this is A-OK
echo "main process exited with $error_code"
