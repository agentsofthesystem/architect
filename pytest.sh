#!/usr/bin/env bash
if [ "$1" == 'setup' ]; then
    pytest --setup-only
elif [ "$1" == 'single' ]; then
    pytest $2 -s
elif [ "$1" == 'coverage' ]; then
    coverage run -m pytest 
    coverage report -m
    coverage html
else
    pytest
fi
