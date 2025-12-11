import scrapy
from bs4 import BeautifulSoup

class WxArticleSpider(scrapy.Spider):
    name = "wx_article"

    # 要爬取的公众号文章链接
    start_urls = [
        "https://mp.weixin.qq.com/s/kVQqjuuZ5SM6xFfbe0CBDw"
    ]

    def parse(self, response):
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # 标题
        title_tag = soup.find(id="activity-name")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # 正文
        content_tag = soup.find(id="js_content")
        content = content_tag.get_text("\n", strip=True) if content_tag else ""

        # 发布时间
        date_tag = soup.find(id="publish_time")
        publish_time = date_tag.get_text(strip=True) if date_tag else ""

        yield {
            "title": title,
            "publish_time": publish_time,
            "content": content
        }
