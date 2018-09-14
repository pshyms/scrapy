# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst, Join
import datetime
from scrapy.loader import ItemLoader
import re


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums


# 去掉tags中的评论字段
def remove_comment_tags(value):
    if "评论" in value:
        return ""
    else:
        return value


# 为front_image_url定义一个空函数，来覆盖TakeFirst()
def return_value(value):
    return value


# 自定义Itemloader, 使取到的字段默认为列表中的第一个元素
class ArticleItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


class ArticleItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field(input_processor=MapCompose(lambda x: x+"-jobbole"))
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
        output_processor=TakeFirst()
    )
    front_image_url = scrapy.Field(output_processor=MapCompose(return_value))
    # 图片下载后在本地的存放路径
    fav_nums = scrapy.Field(input_processor=MapCompose(get_nums))
    tags = scrapy.Field(
        output_processor=Join(","),
        input_processor=MapCompose(remove_comment_tags)
    )
    url = scrapy.Field()
    # 对url进行md5缩减位数
    url_object_id = scrapy.Field()
    content = scrapy.Field()
    front_image_path = scrapy.Field()




