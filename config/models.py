# -*- coding: UTF-8 -*-
from bson import ObjectId
from mongoengine import *


class PageScrapper(Document):
    id = ObjectIdField(primary_key=True, default=lambda: ObjectId())
    job_name = StringField()  # job name
    url = StringField()  # 链接地址
    html = StringField()  # 网页代码
    status = IntField(default=0)  # 0等待 1进行中 2已失败 3已结束
    message = StringField()  # 如果有服务器信息，则处理
    is_del = BooleanField(default=False)
    create_at = LongField()
    update_at = LongField()
    meta = {
        "index_background": True,
        "indexes": [
            {"fields": ("job_name", "url")}
        ]
    }
