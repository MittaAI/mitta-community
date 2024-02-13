#!/bin/bash

while true; do
    screen -dmS gunicorn_screen gunicorn -b :7878 controller:app
    sleep 1
    
    while screen -list | grep -q gunicorn_screen; do
        sleep 10
    done
    
    echo "Gunicorn exited. Restarting..."
    sleep 5
done
