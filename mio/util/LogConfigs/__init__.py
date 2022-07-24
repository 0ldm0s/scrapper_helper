# -*- coding: utf-8 -*-
import logging
from daiquiri.formatter import DatadogFormatter, ColorExtrasFormatter


class DataDog(object):
    hostname: str
    port: int
    formatter: DatadogFormatter
    level: int

    def __init__(self, hostname: str, port: int, formatter: DatadogFormatter, level: int = logging.INFO):
        self.hostname = hostname
        self.port = port
        self.formatter = formatter
        self.level = level


class SysLog(object):
    program_name: str
    facility: str
    formatter: ColorExtrasFormatter
    level: int

    def __init__(self, program_name: str, facility: str, formatter: ColorExtrasFormatter, level: int = logging.INFO):
        self.program_name = program_name
        self.facility = facility
        self.formatter = formatter
        self.level = level
