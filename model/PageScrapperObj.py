# -*- coding: UTF-8 -*-
import inspect
from typing import Tuple, Optional, List
from mongoengine.queryset import Q, QuerySet
from mio.util.Logs import LogHandler
from mio.util.Helper import get_local_now
from config.models import PageScrapper


class PageScrapperObj(object):
    def __get_logger__(self, name: str) -> LogHandler:
        name = "{}.{}".format(self.__class__.__name__, name)
        return LogHandler(name)

    def get(self, **kwargs) -> Optional[PageScrapper]:
        logger = self.__get_logger__(inspect.stack()[0].function)
        try:
            order_by = kwargs.pop("order_by")
        except Exception as e:
            str(e)
            order_by = ["-id"]
        try:
            return PageScrapper.objects(**kwargs).order_by(*order_by).first()
        except Exception as e:
            logger.debug(e)
            return None

    def set_one(
            self, job_name: str, url: str, html: Optional[str] = None, status: Optional[int] = None
    ) -> Optional[PageScrapper]:
        logger = self.__get_logger__(inspect.stack()[0].function)
        try:
            dt = get_local_now(hours=8)
            item: Optional[PageScrapper] = self.get(job_name=job_name, url=url, is_del=False)
            if item is None:
                status = 0 if status is None else status
                item = PageScrapper(
                    job_name=job_name, url=url, html=html, status=status)
                item.create_at = dt
            else:
                if html is not None:
                    item.html = html
                if status is not None:
                    item.status = status
            item.update_at = dt
            item.save()
            return item
        except Exception as e:
            logger.error(e)
            return None

    def get_list(
            self, page: int, per_page: int, job_name: Optional[str] = None, status: Optional[int] = None,
            order_by: Optional[List[str]] = None, is_all: bool = False
    ) -> Tuple[int, List[PageScrapper]]:
        logger = self.__get_logger__(inspect.stack()[0].function)
        if order_by is None:
            order_by = ["-id"]
        total: int = 0
        try:
            query = Q(is_del=False)
            if job_name is not None:
                query = Q(job_name=job_name) & query
            if status is not None:
                query = query & Q(status=status)
            items: QuerySet = PageScrapper.objects(query).order_by(*order_by)
            total = items.count()
            if is_all:
                return total, items.all()
            offset: int = (page - 1) * per_page
            return total, items.skip(offset).limit(per_page)
        except Exception as e:
            logger.error(e)
            return total, []

    @staticmethod
    def quick_save(item: PageScrapper):
        item.update_at = get_local_now(hours=8)
        item.save()
