#!/bin/bash
python -m daphne pratic_django.asgi:application --bind 0.0.0.0 --port 8000 &
python home/server.py &
wait
