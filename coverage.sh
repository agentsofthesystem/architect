#!/usr/bin/env bash
coverage run -m pytest
coverage report --fail-under=30