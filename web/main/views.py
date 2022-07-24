# -*- coding: utf-8 -*-
import os
import sys
from flask import send_from_directory, render_template
from typing import Optional
from mio.util.Helper import get_root_path
from mio.util.Logs import LogHandler
from mio.util.Local import I18n
from . import main

logger = LogHandler('view')


@main.app_template_filter("get_local_text")
def get_local_text(text: str, lang: Optional[str] = None):
    tt = I18n(lang)
    return tt.get_text(text)


@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(get_root_path(), 'web', 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@main.route('/')
def index():
    # logger.debug(u'当前访客的IP地址为:{}'.format(get_real_ip()))
    sys_ver = sys.version
    return render_template('index.html', sys_ver=sys_ver)


@main.route('/client.cfm')
def client_page():
    return render_template('client.html')
