#!/bin/sh
PYENV_ROOT="/usr/local/.pyenv"
PYTHON_ROOT="$PYENV_ROOT/shims"
cd $(dirname $0)
work_path=$(pwd)
mkdir -p "${work_path}/logs"
ulimit -n 512000
# this for docker user
#${PYTHON_ROOT}/circusd --daemon circus.ini
# this for systemd user
${PYTHON_ROOT}/circusd circus.ini