# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from Article.items import LagouJobItemLoader, LagouJobItem
from Article.utils.common import get_md5
from datetime import datetime


class LagouSpider(CrawlSpider):
    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']
    # agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/" \
    #        "537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"

    custom_settings = {
        # 设置为False，cookies将不会发送给web server
        "COOKIES_ENABLED": False,
        # 设置下载延迟
        "DOWNLOAD_DELAY": 1,
        # XHR中的newMessageList.json的请求头里的信息
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
            'Cookie': 'JSESSIONID=ABAAABAAAFCAAEGBC99154D1A744BD8AD12BA0DEE80F320; '
                      'showExpriedIndex=1; showExpriedCompanyHome=1; showExpriedMyPublish=1; '
                      'hasDeliver=0; _ga=GA1.2.1111395267.1516570248; _gid=GA1.2.1409769975.1516570248; '
                      'user_trace_token=20180122053048-58e2991f-fef2-11e7-b2dc-525400f775ce; PRE_UTM=; '
                      'LGUID=20180122053048-58e29cd9-fef2-11e7-b2dc-525400f775ce; '
                      'index_location_city=%E5%85%A8%E5%9B%BD; X_HTTP_TOKEN=7e9c503b9a29e06e6d130f153c562827;'
                      ' _gat=1; LGSID=20180122055709-0762fae6-fef6-11e7-b2e0-525400f775ce; PRE_HOST=github.com;'
                      ' PRE_SITE=https%3A%2F%2Fgithub.com%2Fconghuaicai%2Fscrapy-spider-templetes; '
                      'PRE_LAND=https%3A%2F%2Fwww.lagou.com%2Fjobs%2F4060662.html;'
                      ' Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1516569758,1516570249,1516570359,1516571830;'
                      ' _putrc=88264D20130653A0; login=true; unick=%E7%94%B0%E5%B2%A9;'
                      ' gate_login_token=3426bce7c3aa91eec701c73101f84e2c7ca7b33483e39ba5;'
                      ' LGRID=20180122060053-8c9fb52e-fef6-11e7-a59f-5254005c3644; '
                      'Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1516572053; '
                      'TG-TRACK-CODE=index_navigation; SEARCH_ID=a39c9c98259643d085e917c740303cc7',
            'Host': 'www.lagou.com',
            'Origin': 'https://www.lagou.com',
            'Referer': 'https://www.lagou.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        }
    }

    rules = (
        # 招聘职位详情页
        Rule(LinkExtractor(allow=(r'jobs/\d+.html')), callback='parse_job', follow=True),
        # 首页中点击相关职位类型的链接URL格式如下
        Rule(LinkExtractor(allow=("zhaopin/.*",)), follow=True),
        # 首页中点击公司，然后再点击页面上面的几个公司链接中的招聘职位格式如下
        Rule(LinkExtractor(allow=("gongsi/j\d+.html",)), follow=True),
    )

    # @staticmethod
    def parse_job(self, response):
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("salary", ".job_request .salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        # 职位描述中把里面的<p>也取到
        item_loader.add_css("job_desc", ".job_bt div")
        # 公司位置也整个提取出来，后面再进一步提取
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_value("crawl_time", datetime.now())
        item_loader.add_css("tags", ".position-label li::text")

        job_item = item_loader.load_item()
        return job_item
