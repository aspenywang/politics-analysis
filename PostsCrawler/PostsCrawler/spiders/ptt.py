import logging

from scrapy import FormRequest
from scrapy.exceptions import CloseSpider
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ..items import pttItem
import pytz
import scrapy
import re

class pttSpider(scrapy.Spider):
    MAX_RETRY = 5
    name = "ptt"
    allowed_domains = ["ptt.cc"]
    _retries = 0
    UTC8 = ZoneInfo("Asia/Taipei")
    MAX_AGE = timedelta(hours=5)

    custom_settings = {
        'DOWNLOAD_DELAY': 0.05,
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'AUTOTHROTTLE_ENABLED': True
    }
    boards = ["Gossiping", 'HatePolitics', 'Stock']
    finished_boards: set[str] = set()

    def start_requests(self):
        for board in self.boards:
            url = f"https://www.ptt.cc/bbs/{board}/index.html"
            yield scrapy.Request(url, callback=self.parse,
                                 meta={"board": board, "page": 0})



    def parse(self, response):
        board = response.meta.get("board")       # defensive lookup
        if board in self.finished_boards:
            self.logger.info(f'board: {board} is finished')
            return
        # ---------- 1. Over‑18 gate ----------
        if response.xpath('//div[@class="over18-notice"]'):
            if self._retries < self.MAX_RETRY:
                self._retries += 1
                yield FormRequest.from_response(
                    response,
                    formdata={"yes": "yes"},
                    callback=self.parse,
                    meta=response.meta,          # <── keep everything
                    dont_filter=True             # avoid “duplicate request” filter
                )
            else:
                self.logger.warning("Over‑18 verification failed.")
            return                                 # nothing else to do yet

        # ---------- 2. Parse the index ----------
        titles = (response.xpath("//div[@class='r-list-sep']/preceding::div[@class='title']/a/@href")
                  or response.xpath("//div[@class='title']/a/@href"))

        for href in titles:
            if board in self.finished_boards:
                break                      # we decided to stop while iterating titles
            yield scrapy.Request(
                response.urljoin(href.get()),
                callback=self.parse_post,
                meta={"board": board}
            )

        # ⬇ run this only if we are still crawling this board
        if board not in self.finished_boards:
            next_page = response.xpath(
                '//*[@id="action-bar-container"]/div/div[2]/a[2]/@href'
            ).get()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    callback=self.parse,
                    meta=response.meta
                )



    def parse_post(self, response):
        board = response.meta["board"]
        if board in self.finished_boards:
            return
        # read post time of the *last* post we just opened
        dt_str = response.css('#main-content > div:nth-child(4) > span.article-meta-value::text').get()
        post_dt = datetime.strptime(dt_str, '%a %b %d %H:%M:%S %Y').replace(tzinfo=self.UTC8)

        if datetime.now(self.UTC8) - post_dt > self.MAX_AGE :
            self.logger.info(f"[{board}] reached 24‑hour cutoff; stopping this board")
            self.finished_boards.add(board)
            if len(self.finished_boards) >= len(self.boards):
                raise CloseSpider(reason="Finished Parsing All Posts in the Past 24 hours.")
            return
        else:
            post_dt = datetime.strptime(dt_str, '%a %b %d %H:%M:%S %Y').replace(tzinfo=pytz.timezone('Asia/Taipei'))

            item = pttItem()
            item['board'] = board
            item['title'] = response.css('#main-content > div:nth-child(3) > span.article-meta-value::text').get()
            item['author'] = response.css('#main-content > div:nth-child(1) > span.article-meta-value::text').get()
            item['date'] = post_dt.strftime('%a %b %d %H:%M:%S %Y')
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
            yield item




