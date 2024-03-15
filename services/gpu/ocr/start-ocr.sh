#!/bin/bash

# Activate the Conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ocr

# Function to start Hypercorn
start_hypercorn() {
    screen -dmS hypercorn_screen hypercorn -b 0.0.0.0:8989 app:app -w 8 --timeout 120
}

# Function to check if Hypercorn is running
is_hypercorn_running() {
    screen -list | grep -q hypercorn_screen
}

# Function to wait for Hypercorn to exit
wait_for_hypercorn_exit() {
    while is_hypercorn_running; do
        sleep 10
    done
}

# Start Hypercorn in a loop
while true; do
    start_hypercorn
    wait_for_hypercorn_exit
    echo "Hypercorn exited. Restarting in 5 seconds..."
    sleep 5
done