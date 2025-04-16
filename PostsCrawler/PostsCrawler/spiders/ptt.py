import logging
import datetime
import scrapy
import re

from scrapy import FormRequest

from .. import settings
from ..items import pttItem


class pttSpider(scrapy.Spider):
    name = "ptt"
    allowed_domains = ["ptt.cc"]
    start_urls = ('https://www.ptt.cc/bbs/%s/index.html' % settings.BOARD_NAME,)
    _retries = 0
    MAX_RETRY = 3
    DOWNLOAD_DELAY = 0.5
    _pagesScrapped = 0
    _pagesFailed = 0
    MAX_PAGES = 1
    _posts = 0

    def parse(self, response):
        if response.xpath('//div[@class="over18-notice"]'):
            if self._retries < pttSpider.MAX_RETRY:
                self._retries += 1
                logging.warning(f'retry {self._retries} times...')
                yield FormRequest.from_response(response,
                                                formdata={'yes': 'yes'},
                                                callback=self.parse)
            else:
                logging.warning('Over 18 verification failed.')
        else:

            if response.xpath("//div[@class='r-list-sep']"):
                titles = response.xpath("//div[@class='r-list-sep']/preceding::div[@class='title']/a/@href")
            else:
                titles = response.xpath("//div[@class='title']/a/@href")

            for href in titles:
                yield scrapy.Request(response.urljoin(href.get()), callback=self.parse_content)

            if self._pages < pttSpider.MAX_PAGES:
                next_page = response.xpath(
                    '//*[@id="action-bar-container"]/div/div[2]/a[2]/@href').get()
                if next_page:
                    url = response.urljoin(next_page)
                    logging.warning('follow {}'.format(url))
                    self._pages += 1
                    yield scrapy.Request(url, self.parse)
                else:
                    logging.warning('no next page')
            else:
                logging.warning('max pages reached')


    def parse_content(self, response):
        try:
            item = pttItem()
            item['board'] = response.css('#main-content > div:nth-child(2) > span.article-meta-value::text').get()
            item['title'] = response.css('#main-content > div:nth-child(3) > span.article-meta-value::text').get()
            item['author'] = response.css('#main-content > div:nth-child(1) > span.article-meta-value::text').get()
            dt_str = response.css('#main-content > div:nth-child(4) > span.article-meta-value::text').get()
            item['date'] = datetime.datetime.strptime(dt_str, '%a %b %d %H:%M:%S %Y')
            item['content'] = response.xpath("//*[@id='main-content']/text()[not(ancestor::div[contains(@class, 'push')]) and normalize-space()]").getall()


            ip_line = response.xpath("//span[contains(text(), '來自:')]/text()").get()
            ip_match = re.search(r'來自:\s*([\d.]+)', ip_line or '')
            ip = ip_match.group(1) if ip_match else None
            item['ip'] = ip

            comments = []
            total_score = 0
            for comment in response.xpath('//div[@class="push"]'):
                push_tag = comment.css('span.push-tag::text').get()
                push_user = comment.css('span.push-userid::text').get()
                push_content = comment.css('span.push-content::text').get()

                if push_tag is None or push_user is None or push_content is None:
                    continue  # skip broken comment block

                if '推' in push_tag:
                    score = 1
                    comment_status = '推'
                elif '噓' in push_tag:
                    score = -1
                    comment_status = '噓'
                else:
                    score = 0
                    comment_status = '→'

                total_score += score
                comments.append({
                    'user': push_user,
                    'content': push_content.strip(': ').strip(),
                    'score': score,
                    'status': comment_status
                })

            item['comments'] = comments
            item['score'] = total_score
            item['url'] = response.url
            self._posts += 1
            yield item

        except Exception as e:
            _pagesFailed = 0

            logging.error(f"Failed to parse {response.url}: {e}")
            return



