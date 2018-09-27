# -*- coding: utf-8 -*-
import scrapy
from selenium import webdriver
import time
import pickle
from urllib import parse
import re
from os import path
import os
from datetime import datetime
from scrapy.loader import ItemLoader
from Article.items import ZhihuQuestionItem, ZhihuAnswerItem
from Article.utils.common import get_md5
import json


class ZhihuSelSpider(scrapy.Spider):
    name = 'zhihu_sel'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    # question第一页answer的请求，返回的是一个json文件
    # start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?" \
    #                    "sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2" \
    #                    "Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2" \
    #                    "Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2" \
    #                    "Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2" \
    #                    "Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2C" \
    #                    "is_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2" \
    #                    "Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3" \
    #                    "Dbest_answerer%29%5D.topics&limit={1}&offset={2}"
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}&sort_by=default"


    headers = {
        # HOST就是要访问的域名地址，https://blog.csdn.net/zhangqi_gsts/article/details/50775341
        "HOST": "www.zhihu.com",
        # referer表示从哪个网页跳转过来的，可防止盗链。https://blog.csdn.net/shenqueying/article/details/79426884
        "Referer": "https://www.zhihu.com",
        'User-Agent': "user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/60.0.3112.113 Safari/537.36"
    }

    # 重点：防止被ban
    custom_settings = {
        "COOKIES_ENABLED": True,
        "DOWNLOAD_DELAY": 1
    }

    """
    提取出html页面中的所有url 并跟踪这些url进行一步爬取
    如果提取的url中格式为 /question/xxx 就下载之后直接进入解析函数
    """
    def parse(self, response):
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        # 使用lambda函数对于每一个url进行过滤，如果是true放回列表，返回false去除。
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            # 具体问题以及具体答案的url我们都要提取出来。用或关系实现，要用小括号括起来。因为具体答案的url没斜杠
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                # 这里的group(1)取到的为(.*zhihu.com/question/(\d+))中的内容，类似https://www.zhihu.com/question/57195513
                request_url = match_obj.group(1)
                # callback中一定是传函数名，不能加()进行实例化
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
                # 这里加上break，意思是抓到一个知乎问题后就停止，不再抓取另外一条问题。方便调试，
                # break
            # 如果不是question页面则直接进一步跟踪
            else:
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)


    # 处理question页面， 从页面中提取出具体的question item
    def parse_question(self, response):
        # 处理新版本, 新版本有唯一类QuestionHeader-title来设置标题，老版本没这个类
        if "QuestionHeader-title" in response.text:

            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                # group(2)取到的为(\d+)中的内容
                question_id = int(match_obj.group(2))

            # 使用scrapy默认提供的ItemLoder使代码更简洁，首先实例化
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)

            #item_loader.add_value("url_object_id", get_md5(response.url))
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            # 提取一条回答内容的例子，可参考下
            # response.css(".QuestionAnswers-answers .List-item:nth-child(1) .RichContent-inner span::text").extract()
            # 提取了所有回答内容
            item_loader.add_css("content", ".QuestionAnswers-answers")
            item_loader.add_css("topics", ".QuestionHeader-topics .Tag.QuestionTopic .Popover div::text")
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
            # 这里的watch_user_num 包含Watch 和 click, 在clean data中分离
            item_loader.add_css("watch_user_num", ".NumberBoard-itemValue ::text")
            item_loader.add_value("url", response.url)

            question_item = item_loader.load_item()



        else:
            # 处理老版本页面的item提取(好像已经没有老版页面了我这里放着保险一下),注意title和watch_user_num的提取中"或"的用法
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            item_loader.add_xpath("watch_user_num", "//*[@id='zh-question-side-header-wrap']/text()|"
                                                    "//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()

        # 发起向后台具体answer的接口请求,获得的是一个json文件,请求中每页20个回答，从offset=0开始
        yield scrapy.Request(self.start_answer_url.format(question_id, 5, 0), headers=self.headers,
                             callback=self.parse_answer)
        yield question_item



    # 处理问题的回答字段
    def parse_answer(self, response):
        # json.loads把json字符串转变为python格式的
        ans_json = json.loads(response.text)
        # 判断是否有后续页面，以及下一个页面的URL，就是页面分析中Preview里的paging信息
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()

            #answer_item["url_object_id"] = get_md5(url=answer["url"])
            answer_item["zhihu_id"] = answer["id"]
            answer_item["question_id"] = answer["question"]["id"]
            # 有时候回答是匿名的，此时author字段中没id值，那么就返回None
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["author_name"] = answer["author"]["name"] if "name" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            # 点赞数处理有问题，先注释掉
            # answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["url"] = "https://www.zhihu.com/question/{0}/answer/{1}".format(answer["question"]["id"], answer["id"])
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.now()

            yield answer_item

        # 如果不是最后一个URL，继续请求下一个页面
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)


    # selenium模拟登陆并存储cookie信息到本地，这里没写callback，默认会跳到parse函数
    # start_requests是spider类中的一个函数，这里重写了此类，会覆盖start_url作为爬虫入口
    def start_requests(self):
        browser = webdriver.Chrome()
        browser.get('https://www.zhihu.com/signin')

        input1 = browser.find_element_by_css_selector("input[name=username]")
        input1.send_keys('13880576568')
        input2 = browser.find_element_by_css_selector("input[name=password]")
        input2.send_keys('shiyan823')
        button = browser.find_element_by_class_name('SignFlow-submitButton')
        button.click()

        time.sleep(5)
        zhihu_ookies = browser.get_cookies()
        print(zhihu_ookies)
        cookie_dict = {}
        for cookie in zhihu_ookies:
            base_path = path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cookies')
            f = open(base_path+"/zhihu/" + cookie['name']+'.zhihu', 'wb')
            pickle.dump(cookie, f)
            f.close()
            cookie_dict[cookie['name']] = cookie['value']
        browser.close()
        return [scrapy.Request(url=self.start_urls[0], dont_filter=True, cookies=cookie_dict)]