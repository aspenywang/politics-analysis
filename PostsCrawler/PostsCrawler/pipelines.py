import json
import os

class PostscrawlerPipeline:
    def open_spider(self, spider):
        self.files = {}  # Dictionary to hold open file handles
        self.first_items = {}  # To track commas per file
        os.makedirs("output", exist_ok=True)

    def close_spider(self, spider):
        for file in self.files.values():
            file.write('\n]')
            file.close()

    def process_item(self, item, spider):
        board = item.get('board', 'Unknown')

        if board not in self.files:
            file_path = f'output/{board}.json'
            f = open(file_path, 'w', encoding='utf-8')
            f.write('[\n')
            self.files[board] = f
            self.first_items[board] = True

        f = self.files[board]
        if not self.first_items[board]:
            f.write(',\n')
        else:
            self.first_items[board] = False

        line = json.dumps(dict(item), ensure_ascii=False)
        f.write(line)
        return item
