#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

root_path: str = os.path.abspath(os.path.dirname(__file__) + '/../')
sys.path.append(root_path)
from mio.pymio import app

from mio.ext.cli import CliCommand
from mio.ext.celery import CeleryCommand

app.cli.add_command(CliCommand)
app.cli.add_command(CeleryCommand)
