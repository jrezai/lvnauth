#!/bin/sh
export DISPLAY=:0.0
export PYTHONPATH=$PYTHONPATH:/app/bin:/app/bin/player
python3 /app/bin/startup.py
