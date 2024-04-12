#!/bin/bash

echo "Stopping services..."
date

# Function to check if any PROCESS files exist
is_any_process_file_exists() {
  if [ -f "/opt/mitta-community/services/gpu/ocr/PROCESS-"* ]; then
    return 0 # At least one PROCESS file exists
  else
    return 1 # No PROCESS files exist
  fi
}

# Function to wait for all PROCESS files to disappear
wait_for_all_process_files() {
  local timeout=$1
  local start_time=$(date +%s)

  while is_any_process_file_exists; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))

    if ((elapsed_time >= timeout)); then
      echo "Timeout reached. Forcing shutdown..."
      break
    fi

    echo "PROCESS files still exist. Waiting for them to disappear..."
    sleep 5
  done
}

# Function to stop a process gracefully
stop_process() {
  local process_name=$1
  local pid=$(pgrep -f "$process_name")

  if [ -n "$pid" ]; then
    echo "Stopping $process_name (PID: $pid)..."
    kill -TERM $pid
    sleep 5

    if pgrep -f "$process_name" > /dev/null; then
      echo "$process_name is still running. Forcing termination..."
      kill -KILL $pid
    else
      echo "$process_name stopped successfully."
    fi
  else
    echo "$process_name is not running."
  fi
}

# Stop Hypercorn
stop_process "hypercorn"

# Wait for all PROCESS files to disappear (timeout: 5 minutes)
wait_for_all_process_files 300

# Stop any other processes you need to stop
# stop_process "another_process"

echo "All services stopped."
date