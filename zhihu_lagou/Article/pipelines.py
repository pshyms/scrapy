# -*- coding: utf-8 -*-
import codecs
import json
import pymysql

from twisted.enterprise import adbapi  # 用于数据库异步插入
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter    # 使用scrapy内部库生成json文件


class ArticlePipeline(object):
    def process_item(self, item, spider):
        return item


# 自定义json文件的导出
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


# 调用scrapy提供的json export导出json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('articleexporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()


# 找到文章列表图片本地存储路径
class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        # 有些文章没封面图
        if "front_image_url" in item:
            for ok, value in results:
                image_file_path = value["path"]
            item["front_image_path"] = image_file_path
        return item


# 同步机制把数据存入mysql
class MysqlPipeline(object):
    def __init__(self):
        self.conn = pymysql.connect(host='47.52.136.86', user='test1', password='123', db='article_spider',
                                    charset="utf8mb4", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into article(title, url, create_date, fav_nums, content)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (item["title"], item["url"], item["create_date"],
                                         item["fav_nums"], item["content"]))
        self.conn.commit()


# 使用连接池方法实现数据异步存储
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True,
        )
        # 连接池
        dbpool = adbapi.ConnectionPool("pymysql", **dbparms)
        # 此处相当于实例化pipeline, 要在init中接收
        return cls(dbpool)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常

    # 处理异步插入的异常情况
    def handle_error(self, failure, item, spider):
        print(failure)

    # 执行具体插入
    def do_insert(self, cursor, item):
        # 根据不同的Item构建不同的sql语句并插入到mysql中
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)