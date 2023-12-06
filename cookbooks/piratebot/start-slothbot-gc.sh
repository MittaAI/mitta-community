#!/bin/bash
set -o allexport
conda activate mittabot
screen -dmS flask bash -c "python main.py"
screen -dmS slothbot bash -c "python slothbot.py"