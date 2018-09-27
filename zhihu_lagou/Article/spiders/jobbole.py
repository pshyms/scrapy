# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from urllib import parse
from Article.items import ArticleItem, ArticleItemLoader
from Article.utils.common import get_md5
import datetime
from scrapy.loader import ItemLoader



class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        # 提取当前页所有文章url地址并下载url内容,提取相关信息
        post_nodes = response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            image_url = post_node.css("img::attr(src)").extract_first("")
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url,  post_url),
                          meta={"front_image_url": image_url}, callback=self.parse_detail)

        # 提取下一页url地址并下载
        next_url = response.css(".next.page-numbers::attr(href)").extract_first()
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        # 文章列表标题前的封面图
        front_image_url = response.meta.get("front_image_url", "")
        # title = response.css(".entry-header h1::text").extract()[0]
        # create_date = response.css("p.entry-meta-hide-on-mobile::text").extract()[0].strip().replace("·", "").strip()
        # fav_nums = response.css(".bookmark-btn::text").re('.*?(\d+).*')
        # tag_list = response.css("p.entry-meta-hide-on-mobile a::text").extract()
        # tag_list = [element for element in tag_list if not element.strip().endswith("评论")]
        # tags = ",".join(tag_list)
        # 收藏数可能为空,如果为空fav_nums[0]会抛异常
        # if fav_nums:
        #     fav_nums = int(fav_nums[0])
        # else:
        #     fav_nums = 0
        # content = response.css("div.entry").extract()[0]

        # 将ArticleItem实例化并填充数据
        # article_item = ArticleItem()
        # article_item["url_object_id"] = get_md5(response.url)
        # article_item["title"] = title
        # try:
        #     create_date = datetime.datetime.strptime(create_date, "%Y/%m/%d").date()
        # except Exception as e:
        #     create_date = datetime.datetime.now().date()
        # article_item["create_date"] = create_date
        # article_item["url"] = response.url
        # article_item["front_image_url"] = [front_image_url]
        # article_item["fav_nums"] = fav_nums
        # article_item["content"] = content

        # 通过item loader加载item, 通过item_loader的add_css和add_value方法处理后的数据都是list类型
        item_loader = ArticleItemLoader(item=ArticleItem(), response=response)
        item_loader.add_css("title", ".entry-header h1::text")
        item_loader.add_css("create_date", "p.entry-meta-hide-on-mobile::text")
        item_loader.add_css("fav_nums", ".bookmark-btn::text")
        item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "div.entry")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_value("front_image_url", [front_image_url])
        # 使用load_item()方法填充数据
        article_item = item_loader.load_item()

        # 把article_item传递到pipelines中
        yield article_item

