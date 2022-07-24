# -*- coding: utf-8 -*-
import inspect
from typing import Optional, List
from mio.sys import celery_app
from mio.util.Logs import LogHandler
from model.PageScrapperObj import PageScrapperObj, PageScrapper
from plugins.QuickCache import QuickCache
from config import XVFB_KEY, MOBILE_KEY, HEADLESS_KEY


def get_logger(name='logger') -> LogHandler:
    logger = LogHandler(name)
    return logger


@celery_app.task
def scrapper(task_id: str):
    console_log = get_logger(inspect.stack()[0].function)
    console_log.info(f"开始处理任务[{task_id}]")
    from flask import current_app
    from cli.WorkMan import Daemon as WorkMan
    qc: QuickCache = QuickCache(current_app)
    xvfb: Optional[bool]
    mobile: Optional[bool]
    _, xvfb = qc.cache(XVFB_KEY)
    if xvfb is None:
        xvfb = False
    _, mobile = qc.cache(MOBILE_KEY)
    if mobile is None:
        mobile = False
    _, headless = qc.cache(HEADLESS_KEY)
    if headless is None:
        headless = True
    worker: WorkMan = WorkMan()
    page_scrapper_obj: PageScrapperObj = PageScrapperObj()
    item: Optional[PageScrapper] = page_scrapper_obj.get(id=task_id, is_del=False)
    if item is None:
        console_log.error(f"[{task_id}]未能找到对应到任务")
        return
    links: List[str] = []
    if item.status == 1:
        console_log.error(f"[{task_id}]正在进行中，跳出")
        return
    if item.status == 3:
        console_log.info(f"[{task_id}]已经完成，检查链接情况")
        links = worker.get_links(app=current_app, url=item.url, page_html=item.html)
    if len(links) == 0:
        page_html: str = worker.get_source(item.url, headless=headless, xvfb=xvfb, mobile=mobile)
        if len(page_html) == 0:
            console_log.error("抓取异常！")
            item.status = 2
            page_scrapper_obj.quick_save(item)
            return
        item.status = 3
        item.html = page_html
        page_scrapper_obj.quick_save(item)
        links = worker.get_links(app=current_app, url=item.url, page_html=page_html)
        if len(links) == 0:
            console_log.info("没有需要处理的链接地址")
            return
    for link in links:
        if link == item.url:
            console_log.info("跳过当前页面")
            continue
        console_log.info(f"入库抓取地址[{link}]")
        link_item: Optional[PageScrapper] = page_scrapper_obj.set_one(job_name=item.job_name, url=link)
        if link_item is None:
            console_log.error("写入数据库失败！")
            continue
        if link_item.status == 1:
            console_log.info(f"[{link}]正在抓取中，跳过")
            continue
        if link_item.status == 2:
            console_log.info(f"[{link}]抓取失败，重建")
            page_scrapper_obj.set_one(job_name=item.job_name, url=link, status=0)
            continue
        page_scrapper_obj.set_one(job_name=item.job_name, url=link)
    console_log.info(f"[{task_id}]完成，结束操作")
