# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


import json

class PostscrawlerPipeline:
    def open_spider(self, spider):
        self.file = open('posts.json', 'w', encoding='utf-8')
        self.file.write('[\n')  # Start JSON array
        self.first_item = True

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',\n')
        else:
            self.first_item = False

        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line)
        return item
