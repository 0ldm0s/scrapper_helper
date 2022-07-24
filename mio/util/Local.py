# -*- coding: utf-8 -*-
import os
import gettext
from flask import request, current_app
from typing import Optional
from mio.util.Helper import get_root_path


class I18n(object):
    _tran_: Optional[gettext.GNUTranslations] = None

    @staticmethod
    def __get_language__() -> str:
        language: Optional[str] = request.accept_languages.best_match(current_app.config['LANGUAGES'])
        if language is None:
            return current_app.config['DEFAULT_LANGUAGE']
        return language

    def __init__(self, language: Optional[str] = None, domain: str = 'messages'):
        if language is None or len(language) <= 0:
            language = self.__get_language__()
        try:
            localedir: str = os.path.join(get_root_path(), 'translations')
            self._tran_ = gettext.translation(domain, localedir, languages=[language])
        except FileNotFoundError:
            pass

    def get_text(self, text: str) -> str:
        try:
            if self._tran_ is None:
                return text
            text = self._tran_.gettext(text)
        except Exception as e:
            str(e)
        return text
