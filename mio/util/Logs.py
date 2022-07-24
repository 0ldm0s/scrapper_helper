# -*- coding: utf-8 -*-
import os
import datetime
import daiquiri
import daiquiri.formatter
from typing import Optional
from enum import Enum, unique
from mio.util.Helper import get_root_path
from mio.util.LogConfigs import *


@unique
class LoggerType(Enum):
    CONSOLE = 1
    FILE = 2
    DATADOG = 3
    SYSLOG = 4
    CONSOLE_FILE = 12
    CONSOLE_DATADOG = 13
    CONSOLE_SYSLOG = 14


nameToLevel = {
    'CONSOLE': LoggerType.CONSOLE,
    'FILE': LoggerType.FILE,
    'DATADOG': LoggerType.DATADOG,
    'SYSLOG': LoggerType.SYSLOG,
    'CONSOLE_FILE': LoggerType.CONSOLE_FILE,
    'CONSOLE_DATADOG': LoggerType.CONSOLE_DATADOG,
    'CONSOLE_SYSLOG': LoggerType.CONSOLE_SYSLOG,
}


class LogHandler(object):
    logger: daiquiri.KeywordArgumentAdapter

    def __init__(self, logger_name: str,
                 fmt: Optional[str] = '%(asctime)s [PID %(process)d] [%(levelname)s] %(name)s -> %(message)s',
                 datefmt: Optional[str] = None, logger_type: LoggerType = None, log_level: int = logging.DEBUG,
                 datadog_config: Optional[DataDog] = None, syslog_config: Optional[SysLog] = None):
        formatter: daiquiri.formatter.ColorFormatter = daiquiri.formatter.ColorFormatter(
            fmt=fmt,
            datefmt=datefmt
        )
        console_only = False
        if logger_type == LoggerType.FILE or logger_type == LoggerType.CONSOLE_FILE:
            logger_dir = os.path.join(get_root_path(), 'logs')
            errors_file = os.path.join(logger_dir, 'errors.log')
            everything_file = os.path.join(logger_dir, 'everything.log')
            if not os.path.isdir(logger_dir):
                os.makedirs(logger_dir)
            if logger_type == LoggerType.CONSOLE_FILE:
                daiquiri.setup(level=log_level, outputs=(
                    daiquiri.output.Stream(formatter=formatter),
                    daiquiri.output.File(errors_file, level=logging.ERROR),
                    daiquiri.output.TimedRotatingFile(
                        everything_file,
                        level=log_level,
                        interval=datetime.timedelta(days=1)),
                ))
            else:
                daiquiri.setup(level=log_level, outputs=(
                    daiquiri.output.File(errors_file, level=logging.ERROR),
                    daiquiri.output.TimedRotatingFile(
                        everything_file,
                        level=log_level,
                        interval=datetime.timedelta(days=1)),
                ))
        elif logger_type == LoggerType.DATADOG or logger_type == LoggerType.CONSOLE_DATADOG:
            if datadog_config is None:
                console_only = True
            else:
                if logger_type == LoggerType.CONSOLE_DATADOG:
                    daiquiri.setup(level=log_level, outputs=(
                        daiquiri.output.Stream(formatter=formatter),
                        daiquiri.output.Datadog(hostname=datadog_config.hostname, port=datadog_config.port,
                                                formatter=datadog_config.formatter, level=datadog_config.level),
                    ))
                else:
                    daiquiri.setup(level=log_level, outputs=(
                        daiquiri.output.Datadog(hostname=datadog_config.hostname, port=datadog_config.port,
                                                formatter=datadog_config.formatter, level=datadog_config.level),
                    ))
        elif logger_type == LoggerType.SYSLOG or logger_type == LoggerType.CONSOLE_SYSLOG:
            if syslog_config is None:
                console_only = True
            else:
                if logger_type == LoggerType.CONSOLE_SYSLOG:
                    daiquiri.setup(level=log_level, outputs=(
                        daiquiri.output.Stream(formatter=formatter),
                        daiquiri.output.Syslog(program_name=syslog_config.program_name, facility=syslog_config.facility,
                                               formatter=syslog_config.formatter, level=syslog_config.level),
                    ))
                else:
                    daiquiri.setup(level=log_level, outputs=(
                        daiquiri.output.Syslog(program_name=syslog_config.program_name, facility=syslog_config.facility,
                                               formatter=syslog_config.formatter, level=syslog_config.level),
                    ))
        else:
            console_only = True
        if console_only:
            daiquiri.setup(level=log_level, outputs=(
                daiquiri.output.Stream(formatter=formatter),
            ))
        self.logger = daiquiri.getLogger(logger_name, subsystem='pymio')

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def warning(self, msg):
        self.logger.warning(msg)
