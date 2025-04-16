import random

from .settings import USER_AGENT_LIST, PROXY_LIST


class RandomUserAgent:

    def process_request(self, request, spider):
        # print(request.headers['User-Agent'])
        ua = random.choice(USER_AGENT_LIST)
        request.headers['User-Agent'] =  ua
        pass

class RandomProxy:

    def process_request(self, request, spider):
        proxy = random.choice(PROXY_LIST)
        request.meta['proxy'] = proxy