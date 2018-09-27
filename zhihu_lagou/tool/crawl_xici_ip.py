__author__ = 'Administrator'
import requests
from scrapy.selector import Selector
import pymysql

conn = pymysql.connect(host="47.52.136.86", user="test1", passwd="123", db="article_spider", charset="utf8")
cursor = conn.cursor()


def crawl_ips():
    # 爬取西刺的免费高匿ip代理，并存入数据库
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0"}
    # 取1568页的内容
    for i in range(1568):
        re = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)

        selector = Selector(text=re.text)
        all_trs = selector.css("#ip_list tr")

        ip_list = []
        # 表头也是一个tr，这个要去掉，所以从1开始切片
        for tr in all_trs[1:]:
            # 获取连接速度
            speed_str = tr.css(".bar::attr(title)").extract()[0]
            if speed_str:
                speed = float(speed_str.split("秒")[0])

            # 获取IP, 端口和代理类型
            ip = tr.css("td:nth-child(2)::text").extract()[0]
            port = tr.css("td:nth-child(3)::text").extract()[0]
            proxy_type = tr.css("td:nth-child(6)::text").extract()[0]

            # 把ip信息放到自定义的列表中
            ip_list.append((ip, port, speed, proxy_type))

        # 存入数据库
        for ip_info in ip_list:
            # 注意第3个元素没加引号，因为它表示速度，我们定义为float类型
            cursor.execute(
                "insert proxy_ip(ip, port, speed, proxy_type) VALUES('{0}', '{1}', {2}, '{3}')".format(
                    # 这里的顺序对应ip_list.append的参数位置
                    ip_info[0], ip_info[1], ip_info[2], ip_info[3]
                )
            )

            conn.commit()


# 从数据库中取出IP
class GetIP(object):

    def delete_ip(self, ip):
        # 从数据库中删除无效的ip
        delete_sql = """
            delete from proxy_ip where ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, ip, port):
        # 判断ip是否可用
        http_url = "http://www.baidu.com"
        proxy_url = "//{0}:{1}".format(ip, port)
        try:
            proxy_dict = {"http": proxy_url,
                          "https": proxy_url}
            response = requests.get(http_url, proxies=proxy_dict)

        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False

    # 从数据库中随机获取一个可用的ip
    def get_random_ip(self):

        random_sql = """
              SELECT ip, port FROM proxy_ip
            ORDER BY RAND()
            LIMIT 1
            """
        result = cursor.execute(random_sql)
        # fetchall的返回类型为tuple
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]


            judge_re = self.judge_ip(ip, port)
            if judge_re:

                return "{0}:{1}".format(ip, port)
            else:
                return self.get_random_ip()


# print (crawl_ips())
if __name__ == "__main__":
    get_ip = GetIP()
    get_ip.get_random_ip()
