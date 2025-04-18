from http.client import responses

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
    MAX_AGE = timedelta(hours=24)

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

        if response.xpath("//div[@class='r-list-sep']"):
            raw_rows = response.xpath(
                '//div[@class="r-ent"][following-sibling::div[@class="r-list-sep"]]')
        else:
            raw_rows = response.xpath('//div[@class="r-ent"]')



        next_page = response.xpath(
            '//*[@id="action-bar-container"]/div/div[2]/a[2]/@href'
        ).get()

        next_page = response.urljoin(next_page) if next_page else None

        rows = [
            (row, row.xpath('./div[@class="title"]/a/@href').get())
            for row in raw_rows
        ]
        rows = [(r, h) for (r, h) in rows if h]           # drop deleted posts


        for idx, (_, href) in enumerate(rows):
            meta = {"board": board, "next_page" : None }
            if idx == len(rows) - 1 and next_page:
                print(f'has next page: {next_page}')
                meta["next_page"] = next_page           # ⬅ baton
            yield response.follow(href, callback=self.parse_post, meta=meta)




    def parse_post(self, response):
        if len(self.finished_boards) >= len(self.boards):
            raise CloseSpider(reason= 'Finished Parsing All Posts from the past 24 hours.')

        board = response.meta["board"]

        next_page = response.meta["next_page"] if response.meta["next_page"] else None
        print(f'next page: {next_page}')


        # ── 1. Extract and parse the post time ───────────────────────────────
        dt_str = response.css(
            '#main-content > div:nth-child(4) > span.article-meta-value::text'
        ).get()
        post_dt = datetime.strptime(
                dt_str, '%a %b %d %H:%M:%S %Y'
            ).replace(tzinfo=self.UTC8)

        # ── 2. Age check: just skip if the post is too old ───────────────────
        print('age checking...')
        if datetime.now(self.UTC8) - post_dt > self.MAX_AGE:
            print(f'finished boards:{self.finished_boards}')
            self.finished_boards.add(board)
            return

        # ── 3. Build and yield the item ─────────────────────────────────────
        item = pttItem()
        item['board']   = board
        item['title']   = response.css(
            '#main-content > div:nth-child(3) > span.article-meta-value::text'
        ).get()
        item['author']  = response.css(
            '#main-content > div:nth-child(1) > span.article-meta-value::text'
        ).get()
        item['date']    = post_dt.strftime('%a %b %d %H:%M:%S %Y')
        item['content'] = response.xpath(
            "//*[@id='main-content']/text()[not(ancestor::div[contains(@class,'push')]) "
            "and normalize-space()]"
        ).getall()

        ip_line  = response.xpath("//span[contains(text(),'來自:')]/text()").get()
        ip_match = re.search(r'來自:\s*([\d.]+)', ip_line or '')
        item['ip'] = ip_match.group(1) if ip_match else None

        comments, total_score = [], 0
        for push in response.xpath('//div[@class="push"]'):
            tag   = push.css('span.push-tag::text').get()
            user  = push.css('span.push-userid::text').get()
            text  = push.css('span.push-content::text').get()
            if not all([tag, user, text]):
                continue

            if '推' in tag:
                score, status = 1, '推'
            elif '噓' in tag:
                score, status = -1, '噓'
            else:
                score, status = 0, '→'

            total_score += score
            comments.append({'user': user, 'content': text.strip(': ').strip(),
                             'score': score, 'status': status})

        item['comments'] = comments
        item['score']    = total_score
        item['url']      = response.url
        print(f'yielding item: {item["title"]} from {item['board']}')
        yield item

        if next_page and board not in self.finished_boards:
            print('proceeding to next page...')
            yield response.follow(
                next_page,
                callback=self.parse,
                meta={"board": board})
        else:
            return
