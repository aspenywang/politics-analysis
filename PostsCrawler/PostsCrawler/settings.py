
import asyncio
import json
import os
import time

from Proxy.proxy import Proxy

BOT_NAME = "PostsCrawler"
LOG_LEVEL = 'WARNING'
SPIDER_MODULES = ["PostsCrawler.spiders"]
NEWSPIDER_MODULE = "PostsCrawler.spiders"
BOARD_NAME = 'Gossiping'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "PostsCrawler (+http://www.yourdomain.com)"

# Obey robots.txt rules
USER_AGENT_LIST = []

with open("./user-agents.json", "r") as f:
    data = json.load(f)
    USER_AGENT_LIST = [entry["ua"] for entry in data]
# Obey robots.txt rules
ROBOTSTXT_OBEY = False

PROXY_LIST = []

# Open the CSV file with proper encoding handling

# Then process the proxies list
PROXY_LIST = []
proxy_fetcher = Proxy()
proxy_fetcher.test_url = "https://www.ptt.cc/bbs/index.html"
proxy_fetcher.speed_threshold = 3

proxy_file = "./Proxy/proxies_list.txt"

# Check if the file exists and its last modification time
if not os.path.exists(proxy_file) or (time.time() - os.path.getmtime(proxy_file)) > 3600:
    asyncio.run(proxy_fetcher.get_proxy_list())

# Read the proxy list from the file
with open(proxy_file, "r") as f:
    data = f.readlines()
    for proxy in data:
        PROXY_LIST.append(proxy.strip())

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "PostsCrawler.middlewares.PostscrawlerSpiderMiddleware": 543,
#}


DOWNLOADER_MIDDLEWARES = {
      "PostsCrawler.middlewares.RandomUserAgent": 750,
    # "PostsCrawler.middlewares.RandomProxy": 750,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "PostsCrawler.pipelines.PostscrawlerPipeline": 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
