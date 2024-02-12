#!/bin/bash

while true; do
    screen -dmS gunicorn_screen gunicorn -b 0.0.0.0:8989 instructor:app -w 2 --timeout 120
    sleep 1
    
    while screen -list | grep -q gunicorn_screen; do
        sleep 10
    done
    
    echo "Gunicorn exited. Restarting..."
    sleep 5
done

