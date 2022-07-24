#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

root_path: str = os.path.abspath(os.path.dirname(__file__) + '/../')
sys.path.append(root_path)
from tornado.httpserver import HTTPServer
from tornado.web import Application, FallbackHandler
from typing import Optional, Union
from mio.sys import create_app, init_timezone, init_uvloop, get_cpu_limit, get_logger_level, get_buffer_size, \
    get_event_loop, os_name
from mio.sys.wsgi import WSGIContainerWithThread
from mio.util.Helper import write_txt_file, is_number, str2int
from config import MIO_HOST, MIO_PORT

MIO_CONFIG: str = os.environ.get('MIO_CONFIG') or 'default'
MIO_APP_CONFIG: str = os.environ.get('MIO_APP_CONFIG') or 'config'
MIO_LIMIT_CPU: int = get_cpu_limit()
pid_file_path: Optional[str] = os.environ.get('MIO_PID_FILE') or None
domain_socket: Optional[str] = os.environ.get('MIO_DOMAIN_SOCKET') or None
MIO_UVLOOP: Union[str, bool] = str(os.environ.get('MIO_UVLOOP', '0'))
MIO_UVLOOP = True if MIO_UVLOOP == '1' else False
init_timezone()
if MIO_UVLOOP:
    init_uvloop()
for arg in sys.argv:
    if not arg.startswith('--'):
        continue
    arg = arg[2:]
    temp = arg.split('=')
    if temp[0].lower() == 'app_config':
        MIO_APP_CONFIG: str = temp[1]
        continue
    if temp[0].lower() == 'host':
        MIO_HOST: str = temp[1]
        os.environ["MIO_HOST"] = MIO_HOST
        continue
    if temp[0].lower() == 'port':
        try:
            port: int = int(temp[1])
            MIO_PORT = port
            os.environ["MIO_PORT"] = str(MIO_PORT)
        except Exception as e:
            print(e)
            exit()
        continue
    if temp[0].lower() == 'config':
        MIO_CONFIG = temp[1]
        continue
    if temp[0].lower() == 'pid':
        pid_file_path: str = temp[1]
        continue
    if temp[0].lower() == 'cpu_limit':
        if os_name in ["windows", "unkonw"]:
            # 不可在windows下设置cpu数
            continue
        MIO_LIMIT_CPU = 1 if not is_number(temp[1]) else str2int(temp[1])
        continue
    if temp[0].lower() == 'ds':
        domain_socket = temp[1]
        continue
if pid_file_path is not None:
    write_txt_file(pid_file_path, str(os.getpid()))
log_level, log_type, is_debug = get_logger_level(MIO_CONFIG)
max_buffer_size, max_body_size = get_buffer_size()
app, wss, console_log = create_app(MIO_CONFIG, root_path, MIO_APP_CONFIG, log_level=log_level, logger_type=log_type)
wss.append((r'.*', FallbackHandler, dict(fallback=WSGIContainerWithThread(app))))
mWSGI: Application = Application(wss, debug=is_debug, autoreload=False)

if __name__ == '__main__':
    try:
        server = HTTPServer(mWSGI, max_buffer_size=max_buffer_size, max_body_size=max_body_size)
        if domain_socket is not None:
            from tornado.netutil import bind_unix_socket

            socket = bind_unix_socket(domain_socket, mode=0o777)
            server.add_socket(socket)
            console_log.info(f'WebServer listen in {domain_socket}')
        else:
            server.bind(MIO_PORT, MIO_HOST)
            console_log.info("WebServer listen in {}://{}:{}".format('http', MIO_HOST, MIO_PORT))
        if MIO_LIMIT_CPU <= 0:
            import multiprocessing

            workers = multiprocessing.cpu_count()
            server.start(workers)
        else:
            server.start(MIO_LIMIT_CPU)
        # 性能下降巨大，最好不要用单例模式
        # 哪怕报告警也不应舍弃fork模式
        get_event_loop().run_forever()
    except KeyboardInterrupt:
        get_event_loop().stop()
        console_log.info("WebServer Closed.")
