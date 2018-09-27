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
from w3lib.html import remove_tags
from Article.settings import SQL_DATETIME_FORMAT
from Article.utils.common import extract_num, extract_num_include_dot


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


# 伯乐在线item类
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

    def get_insert_sql(self):
        insert_sql = """
            insert into article(title, url, create_date, fav_nums)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (self["title"], self["url"], self["create_date"], self["fav_nums"])
        return insert_sql, params


# 知乎问题的item
class ZhihuQuestionItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_ask(zhihu_id, topics, url, title, content, answer_num, comments_num,
              watch_user_num, click_num, crawl_time
              )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUES(content), answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
              watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
        """

        # scrapy.Field返回类型为列表
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        # extract_num就是上面定义的get_nums，只是把它重新定义为一个常用函数了
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))

        # 浏览数和点击数是一起取出来的，并且用逗号分隔，需要单独取出来
        if len(self["watch_user_num"]) == 2:
            watch_user_num_click = self["watch_user_num"]
            watch_user_num = extract_num_include_dot(watch_user_num_click[0])
            click_num = extract_num_include_dot(watch_user_num_click[1])
        else:
            watch_user_num_click = self["watch_user_num"]
            watch_user_num = extract_num_include_dot(watch_user_num_click[0])
            click_num = 0

        # 要把时间格式转为字符串格式
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        # 顺序要和sql语句中的保持一样
        params = (zhihu_id, topics, url, title, content, answer_num, comments_num,
                  watch_user_num, click_num, crawl_time)

        return insert_sql, params


# 知乎回答的item
class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    author_name = scrapy.Field()
    content = scrapy.Field()
    #praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, author_name, content, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),
              update_time=VALUES(update_time)
        """

        # int类型转为datetime类型，需要使用fromtimestamp函数；再转为字符串类型，需要strftime函数
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)

        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["author_name"], self["content"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params











# 去掉拉钩网工作城市的斜线
def remove_splash(value):
    return value.replace("/", "")


# 处理工作地点中的空格和不需要的信息
def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


# 给拉钩网定义item loader
class LagouJobItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


# 拉钩网职位信息
class LagouJobItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(input_processor=MapCompose(remove_splash))
    work_years = scrapy.Field(input_processor=MapCompose(remove_splash))
    degree = scrapy.Field(input_processor=MapCompose(remove_splash))
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    tags = scrapy.Field(input_processor=Join(","))
    job_desc = scrapy.Field(input_processor=MapCompose(remove_tags))
    job_addr = scrapy.Field(input_processor=MapCompose(remove_tags, handle_jobaddr))
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou(title, url, url_object_id, salary, job_city, work_years, degree,
            publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
            tags, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc)
        """
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"],
            self["work_years"], self["degree"],
            self["publish_time"], self["job_advantage"], self["job_desc"],
            self["job_addr"], self["company_name"], self["company_url"], self["tags"],
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params




