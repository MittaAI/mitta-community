#!/bin/bash

echo "Stopping services..."
date#!/bin/bash

# Function to check if a process is running
is_process_running() {
    if pgrep -f "$1" > /dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}

# Function to stop a process gracefully
stop_process() {
    local process_name=$1
    local pid=$(pgrep -f "$process_name")
    
    if [ -n "$pid" ]; then
        echo "Stopping $process_name (PID: $pid)..."
        kill -TERM $pid
        sleep 5
        
        if is_process_running "$process_name"; then
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

# Stop any other processes you need to stop
# stop_process "another_process"

echo "All services stopped."
date