# -*- coding: utf-8 -*-
import os
import asyncio
from tornado import escape, gen
from tornado import httputil
from tornado.httputil import ResponseStartLine, HTTPHeaders, HTTPServerRequest
from tornado.wsgi import WSGIContainer
from typing import List, Tuple, Optional, Callable, Any, Type, Dict, Union
from types import TracebackType

MIO_SYSTEM_VERSION = '1.6.0'


class WSGIContainerWithThread(WSGIContainer):
    @gen.coroutine
    def __call__(self, request: HTTPServerRequest):
        data: Dict[str, Any] = {}
        response: List[bytes] = []

        def start_response(
                status: str,
                http_headers: List[Tuple[str, str]],
                exec_info: Optional[
                    Tuple[
                        Optional[Type[BaseException]],
                        Optional[BaseException],
                        Optional[TracebackType],
                    ]
                ] = None,
        ) -> Callable[[bytes], Any]:
            data['status'] = status
            data['headers'] = http_headers
            if exec_info:
                print(exec_info)
            return response.append

        loop = asyncio.get_event_loop()
        app_response = yield loop.run_in_executor(
            None, self.wsgi_application, WSGIContainer.environ(request), start_response)
        try:
            response.extend(app_response)
            body: bytes = b''.join(response)
        finally:
            if hasattr(app_response, 'close'):
                app_response.close()
        if not data:
            raise Exception('WSGI app did not call start_response')
        status_code_str, reason = str(data['status']).split(' ', 1)
        status_code: int = int(status_code_str)
        headers: List[tuple] = data['headers']
        header_set = set(k.lower() for (k, v) in headers)
        body = escape.utf8(body)
        if status_code != 304:
            if 'content-length' not in header_set:
                headers.append(('Content-Length', str(len(body))))
            if 'content-type' not in header_set:
                headers.append(('Content-Type', 'text/html; charset=UTF-8'))
        show_version: Union[str, bool] = os.environ.get("MIO_SERVER_TAG", "0")
        show_version = True if show_version == '1' else False
        server: str = f"PyMio/{MIO_SYSTEM_VERSION}" if show_version else "PyMio"
        headers.append(('Server', server))
        start_line: ResponseStartLine = httputil.ResponseStartLine('HTTP/1.1', status_code, reason)
        header_obj: HTTPHeaders = httputil.HTTPHeaders()
        for key, value in headers:
            header_obj.add(key, value)
        assert request.connection is not None
        request.connection.write_headers(start_line, header_obj, chunk=body)
        request.connection.finish()
        self._log(status_code, request)
