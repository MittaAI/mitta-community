#!/bin/bash

# Activate the Conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate instructor

# Function to start Gunicorn
start_gunicorn() {
    screen -dmS gunicorn_screen gunicorn -b 0.0.0.0:8989 app:app -w 2 --timeout 120
}

# Function to check if Gunicorn is running
is_gunicorn_running() {
    screen -list | grep -q gunicorn_screen
}

# Function to wait for Gunicorn to exit
wait_for_gunicorn_exit() {
    while is_gunicorn_running; do
        sleep 10
    done
}

# Start Gunicorn in a loop
while true; do
    start_gunicorn
    wait_for_gunicorn_exit
    echo "Gunicorn exited. Restarting in 5 seconds..."
    sleep 5
done
