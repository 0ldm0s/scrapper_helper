# -*- coding: utf-8 -*-
import sys
import click
from celery.__main__ import main
from flask.cli import AppGroup
from typing import List

CeleryCommand: AppGroup = AppGroup('celery', help='celery helper')


@CeleryCommand.command('run')
@click.option('-A', '--app', 'clazz', default=None,
              help=u'APPLICATION.')
@click.option('-w', '--worker', 'worker', default=None,
              help=u'Celery worker args.')
@click.option('-ctl', '--control', 'control', default=None,
              help=u'Workers remote control args.')
def run(clazz=None, worker=None, control=None):
    if clazz is None:
        print(u'App must be set.')
        exit(0)
    cmd_lines: List[str] = ['celery', '-A', clazz]
    if worker is not None:
        cmd_lines.append('worker')
        tmp: List[str] = str(worker).split(' ')
        for _cmd_ in tmp:
            if len(_cmd_) <= 0:
                continue
            if _cmd_.find('=') >= 0:
                _cmd_ = '--' + _cmd_
            else:
                _cmd_ = '-' + _cmd_
            cmd_lines.append(_cmd_)
    if worker is None and control is not None:
        cmd_lines.append('control')
        tmp: List[str] = str(control).split(' ')
        for _cmd_ in tmp:
            if len(_cmd_) <= 0:
                continue
            if _cmd_.find('=') >= 0:
                _cmd_ = '--' + _cmd_
            else:
                _cmd_ = '-' + _cmd_
            cmd_lines.append(_cmd_)
    sys.argv = cmd_lines
    sys.exit(main())
