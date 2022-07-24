# -*- coding: utf-8 -*-
import os
import csv
import time
import pycurl
import shutil
import inspect
import configparser
from configparser import ConfigParser
from io import StringIO
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from flask import Flask
from urllib.parse import urlparse
from selenium.webdriver import FirefoxProfile, FirefoxOptions
from typing import Union, Optional, List, Dict, Any
from mio.sys import os_name
from mio.util.Helper import get_args_from_dict, get_root_path, write_txt_file, read_txt_file
from mio.util.Logs import LogHandler
from model.PageScrapperObj import PageScrapperObj, PageScrapper
from plugins import helium
from plugins.QuickCache import QuickCache
from config import XVFB_KEY, MOBILE_KEY, HEADLESS_KEY, BLACK_KEYWORDS_KEY
from cli.celery.Worker import scrapper


class Daemon(object):
    def __get_logger__(self, name: str) -> LogHandler:
        name = '{}.{}'.format(self.__class__.__name__, name)
        return LogHandler(name)

    def get_links(self, app: Flask, url: str, page_html: str) -> List[str]:
        parts = urlparse(url)
        console_log = self.__get_logger__(inspect.stack()[0].function)
        console_log.info(f"开始解析[{url}]中包含的链接")
        links: List[str] = []
        qc: QuickCache = QuickCache(app)
        black_keywords: Optional[List[str]]
        _, black_keywords = qc.cache(BLACK_KEYWORDS_KEY)
        if black_keywords is None:
            black_keywords = []
        _soup_: BeautifulSoup = BeautifulSoup(page_html, "html.parser")
        links_rows: ResultSet = _soup_.find_all("a", href=True)
        for _row_ in links_rows:
            href: str = _row_.get("href", "")
            text: str = _row_.getText()
            href = href.strip()
            if len(href) == 0 or href == "/":
                console_log.info("无需处理的链接")
                continue
            block: bool = False
            for _word_ in black_keywords:
                if _word_ in href.lower():
                    console_log.info(f"链接匹配到黑名单词[{_word_}]")
                    block = True
                    break
                if _word_ in text.lower():
                    console_log.info(f"链接文本匹配到黑名单词[{_word_}]")
                    block = True
                    break
            if block:
                continue
            base_url: str = f"{parts.scheme}://{parts.netloc}"
            if href.lower().startswith("http"):
                if parts.netloc not in href.lower():
                    continue
                if href in links:
                    continue
                if base_url == href.lower():
                    continue
                links.append(href)
                continue
            if href.lower().startswith("/"):
                base_url = f"{base_url}{href}"
            else:
                path: str = parts.path
                if not path.endswith("/"):
                    path = path + "/"
                base_url = f"{base_url}{path}{href}"
            if base_url in links:
                continue
            links.append(base_url)
        return links

    def get_source(
            self, url: str, headless: bool = True, xvfb: bool = False, mobile: bool = False, image: bool = True,
            javascript: bool = True
    ) -> str:
        console_log = self.__get_logger__(inspect.stack()[0].function)
        display = None
        if xvfb:
            from pyvirtualdisplay import Display
            display: Display = Display(visible=0, size=(1440, 900))
            display.start()
            # 虚拟屏最好不要用无头
            headless = False
        profile = FirefoxProfile()
        if not image:
            profile.set_preference('permissions.default.image', 2)
        if not javascript:
            profile.set_preference("javascript.enabled", False)
        if mobile:
            ua: str = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, " \
                      "like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            profile.set_preference("general.useragent.override", ua)
        profile.set_preference("browser.privatebrowsing.autostart", True)
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference('network.proxy.type', 1)
        profile.set_preference('network.proxy.socks', "127.0.0.1")
        profile.set_preference('network.proxy.socks_port', 9050)
        profile.set_preference("network.proxy.socks_remote_dns", True)
        opts = FirefoxOptions()
        opts.profile = profile
        page_source: str = ""
        try:
            console_log.info(f"开始处理[{url}]")
            helium.start_firefox(options=opts, headless=headless)
            helium.go_to(url)
            time.sleep(1)
            page_source = helium.get_rendered_source()
        except Exception as e:
            console_log.error(e)
        finally:
            helium.kill_browser()
            if display:
                console_log.info("关闭虚拟屏")
                display.stop()
            return page_source

    def __download_file__(self, url: str, filename: str) -> bool:
        console_log = self.__get_logger__(inspect.stack()[0].function)
        try:
            with open(filename, "wb") as fp:
                curl = pycurl.Curl()
                curl.setopt(pycurl.URL, url)
                curl.setopt(pycurl.SSL_VERIFYPEER, 1)
                curl.setopt(pycurl.SSL_VERIFYHOST, 2)
                curl.setopt(pycurl.WRITEDATA, fp)
                curl.perform()
                curl.close()
            return True
        except Exception as e:
            console_log.error(e)
            return False

    def download_files(self, app: Flask, kwargs: Dict[str, Any]):
        id(app), id(kwargs)
        console_log = self.__get_logger__(inspect.stack()[0].function)
        config_file: str = os.path.join(get_root_path(), "scrapper.ini")
        if not os.path.isfile(config_file):
            console_log.error(f"[{config_file}]不存在")
            return
        config: ConfigParser = configparser.ConfigParser()
        config.read(config_file)
        if "Base" not in config:
            console_log.error("配置文件异常")
            return
        home: str = get_args_from_dict(config["Base"], "home", force_str=True)
        job_name: str = get_args_from_dict(config["Base"], "job_name", force_str=True)
        if len(job_name) == 0:
            console_log.error("未指定抓取的任务名")
            return
        if len(home) == 0 or not home.lower().startswith("http"):
            console_log.info("未指定根域名")
            return
            # 创建基础文件夹
        web_root: str = os.path.join(get_root_path(), "gen_html", job_name)
        if not os.path.isdir(web_root):
            console_log.error("请先生成html文件")
            return
        g = os.walk(web_root)
        for path, _, file_list in g:
            for file_name in file_list:
                file_name = str(file_name).strip()
                full_name = os.path.join(path, file_name)
                if not full_name.endswith(".html") and not full_name.endswith(".htm") and \
                        not full_name.endswith(".php"):
                    continue
                page_html: str = read_txt_file(full_name)
                _soup_: BeautifulSoup = BeautifulSoup(page_html, "html.parser")
                img_list: ResultSet = _soup_.find_all("img", src=True)
                for _img_ in img_list:
                    href: str = _img_.get("src", "")
                    if len(href) == 0:
                        continue
                    if href.lower().startswith("http"):
                        # 站外暂不处理
                        continue
                    paths: List[str] = href.split("/")
                    filename: str = paths.pop(-1)
                    if "." not in filename:
                        return
                    download_path: str = os.path.join(web_root, *paths)
                    if not os.path.isdir(download_path):
                        os.makedirs(download_path)
                    full_file: str = os.path.join(download_path, filename)
                    if os.path.isfile(full_file):
                        console_log.info(f"文件[{filename}]已存在，跳过")
                        continue
                    download_url: str = f"{home}{href}"
                    console_log.info(f"开始下载[{download_url}]")
                    is_ok: bool = self.__download_file__(download_url, full_file)
                    if is_ok:
                        console_log.info("下载结束")
                        continue
                    console_log.info("下载失败")
                    shutil.rmtree(full_file)
                script_list: ResultSet = _soup_.find_all("script", src=True)
                for _rel_ in script_list:
                    href: str = _rel_.get("src", "")
                    if len(href) == 0:
                        continue
                    if not href.lower().endswith(".js"):
                        continue
                    download_url: str
                    if not href.lower().startswith("http"):
                        # FIXME 这里暂时偷懒下
                        download_url = f"{home}{href}"
                    else:
                        # FIXME 暂时不处理站外数据
                        continue
                    paths: List[str] = href.split("/")
                    filename: str = paths.pop(-1)
                    download_path: str = os.path.join(web_root, *paths)
                    if not os.path.isdir(download_path):
                        os.makedirs(download_path)
                    full_file: str = os.path.join(download_path, filename)
                    if os.path.isfile(full_file):
                        console_log.info(f"文件[{filename}]已存在，跳过")
                        continue
                    console_log.info(f"开始下载[{download_url}]")
                    is_ok: bool = self.__download_file__(download_url, full_file)
                    if is_ok:
                        console_log.info("下载结束")
                        continue
                    console_log.info("下载失败")
                    shutil.rmtree(full_file)
                rel_list: ResultSet = _soup_.find_all("link", href=True)
                for _rel_ in rel_list:
                    href: str = _rel_.get("href", "")
                    if len(href) == 0:
                        continue
                    if not href.lower().endswith(".js") and not href.lower().endswith(".css") and \
                            not href.lower().endswith(".ico"):
                        continue
                    download_url: str
                    if not href.lower().startswith("http"):
                        # FIXME 这里暂时偷懒下
                        download_url = f"{home}{href}"
                    else:
                        # FIXME 暂时不处理站外数据
                        continue
                    paths: List[str] = href.split("/")
                    filename: str = paths.pop(-1)
                    download_path: str = os.path.join(web_root, *paths)
                    if not os.path.isdir(download_path):
                        os.makedirs(download_path)
                    full_file: str = os.path.join(download_path, filename)
                    if os.path.isfile(full_file):
                        console_log.info(f"文件[{filename}]已存在，跳过")
                        continue
                    console_log.info(f"开始下载[{download_url}]")
                    is_ok: bool = self.__download_file__(download_url, full_file)
                    if is_ok:
                        console_log.info("下载结束")
                        continue
                    console_log.info("下载失败")
                    shutil.rmtree(full_file)
        console_log.info("任务结束")

    def gen_html(self, app: Flask, kwargs: Dict[str, Any]):
        id(app), id(kwargs)
        console_log = self.__get_logger__(inspect.stack()[0].function)
        config_file: str = os.path.join(get_root_path(), "scrapper.ini")
        if not os.path.isfile(config_file):
            console_log.error(f"[{config_file}]不存在")
            return
        config: ConfigParser = configparser.ConfigParser()
        config.read(config_file)
        if "Base" not in config:
            console_log.error("配置文件异常")
            return
        job_name: str = get_args_from_dict(config["Base"], "job_name", force_str=True)
        if len(job_name) == 0:
            console_log.error("未指定抓取的任务名")
            return
        # 创建基础文件夹
        web_root: str = os.path.join(get_root_path(), "gen_html", job_name)
        if not os.path.isdir(web_root):
            os.makedirs(web_root)
        # 开始读入数据
        total, items = PageScrapperObj().get_list(0, 0, job_name=job_name, status=3, is_all=True)
        if total == 0:
            console_log.info("无事可做")
            return
        for link_item in items:
            parts = urlparse(link_item.url)
            path: str = parts.path
            path_list: List[str] = path.split("/")
            filename: str = path_list[-1]
            if "." not in filename:
                filename = "index.html"
            if filename != "index.html":
                path_list.pop(-1)
            path = os.path.join(web_root, *path_list)
            if not os.path.isdir(path):
                os.makedirs(path)
            full_name: str = os.path.join(path, filename)
            console_log.info(f"正在生成[{full_name}]")
            write_txt_file(full_name, link_item.html)
        console_log.info("操作全部完成")

    def do_scrapper(self, app: Flask, kwargs: Dict[str, Any]):
        id(kwargs)
        console_log = self.__get_logger__(inspect.stack()[0].function)
        config_file: str = os.path.join(get_root_path(), "scrapper.ini")
        if not os.path.isfile(config_file):
            console_log.error(f"[{config_file}]不存在")
            return
        config: ConfigParser = configparser.ConfigParser()
        config.read(config_file)
        if "Base" not in config:
            console_log.error("配置文件异常")
            return
        home: str = get_args_from_dict(config["Base"], "home", force_str=True)
        job_name: str = get_args_from_dict(config["Base"], "job_name", force_str=True)
        black_keywords_str: str = get_args_from_dict(config["Base"], "black_keywords", force_str=True)
        if len(home) == 0:
            console_log.error("未指定抓取的网址")
            return
        if len(job_name) == 0:
            console_log.error("未指定抓取的任务名")
            return
        if not home.lower().startswith("http://") and not home.lower().startswith("https://"):
            console_log.error("网址必须由http或https开头")
            return
        black_keywords: List[str] = []
        if len(black_keywords_str) > 0:
            reader = csv.reader(StringIO(black_keywords_str), delimiter=",")
            for row in reader:
                for word in row:
                    word = word.strip()
                    if len(word) == 0:
                        continue
                    if word in black_keywords:
                        continue
                    black_keywords.append(word)
        qc: QuickCache = QuickCache(app)
        qc.cache(BLACK_KEYWORDS_KEY, black_keywords)
        console_log.info(f"计划抓取的主页地址为:[{home}]")
        xvfb: Union[str, bool] = str(get_args_from_dict(config["Base"], "xvfb", force_str=True)).lower()
        xvfb = True if xvfb == "true" or xvfb == "1" else False
        # 如果是window，则强制不使用虚拟屏
        if os_name in ["unkonw", "windows"]:
            xvfb = False
        qc.cache(XVFB_KEY, xvfb)
        mobile: Union[str, bool] = str(get_args_from_dict(config["Base"], "mobile", force_str=True)).lower()
        mobile = True if mobile == "true" or mobile == "1" else False
        qc.cache(MOBILE_KEY, mobile)
        headless: Union[str, bool] = str(get_args_from_dict(config["Base"], "headless", force_str=True)).lower()
        headless = True if headless == "true" or headless == "1" else False
        qc.cache(HEADLESS_KEY, headless)
        page_scrapper_obj: PageScrapperObj = PageScrapperObj()
        status: Optional[int]
        page_html: str = ""
        item: Optional[PageScrapper] = page_scrapper_obj.get(job_name=job_name, url=home, is_del=False)
        if item is None:
            status = 0
        else:
            status = 0 if item.status != 3 else 3
            page_html = item.html
        if status == 0:
            page_html = self.get_source(home, headless=headless, xvfb=xvfb, mobile=mobile)
            status = 3
        if len(page_html) == 0:
            console_log.error("抓取异常！")
            return
        page_scrapper_obj.set_one(job_name=job_name, url=home, html=page_html, status=status)
        console_log.info("开始分析源码")
        links: List[str] = self.get_links(app=app, url=home, page_html=page_html)
        for link in links:
            console_log.info(f"入库抓取地址[{link}]")
            link_item: Optional[PageScrapper] = page_scrapper_obj.set_one(job_name=job_name, url=link)
            if link_item.status in [1, 2]:
                # 强制归零
                link_item.status = 0
                page_scrapper_obj.quick_save(link_item)
        while True:
            # 实际这里不应该这么处理，这是只单线的时候可用
            total, items = page_scrapper_obj.get_list(0, 0, job_name=job_name, status=0, is_all=True)
            if total == 0:
                break
            for link_item in items:
                scrapper(str(link_item.id))
        console_log.info("结束任务")
