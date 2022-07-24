#!/bin/bash
export PYTHONIOENCODING=utf-8
find . -name "*.pyc" | xargs rm -f
python -m compileall .
python pack.py