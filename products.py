import conn
import requests
import os
import urllib3
import re
import math
import time
import random
import pytesseract

from lxml.html import fromstring
from bs4 import BeautifulSoup
from PIL import Image


# 获取html代码
def get_html_text(url):
    try:
        headers = {
            'content-type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 '
                          '(KHTML, like Gecko) Version/5.1 Safari/534.50'
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'  # 把编码改为utf-8
        text = response.content
        return text

    except:
        conn.request_fail.insert({'url': url, 'datetime': time.time()})
        return 'Error!'


def parse_products_part_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    print(soup.prettify())
    product_areas = soup.find_all('ul', class_='catfiltersub')
    for area in product_areas:
        for products in area.find_all('li'):
            part = products.a.text
            r = r'\((.*?)\)'
            count = re.findall(r, products.text)[0].replace(' 项', '')
            href = 'https://www.digikey.cn' + products.find('a')['href']
            products_part_info = {
                'part': part,
                'count': int(count),
                'href': href,
                'crawled': 0
            }
            # print(products_part_info)
            save_products_part(products_part_info)

    return ''


# 存储products part信息
def save_products_part(products_part):
    exists = exists_products_part(products_part['part'])
    if not exists:
        conn.products_part.insert(products_part)


# 判断products part否已经存在
def exists_products_part(products_part):
    product_count = conn.products_part.count({'part': products_part})
    if product_count > 0:
        return True
    else:
        return False


# 获取产品filed value
def get_product_field_value():
    products_part = conn.products_part.find({"crawled": 0}).limit(1)
    for product_part in products_part:
        _id = product_part['_id']
        url = product_part['href']
        text = get_html_text(url)
        soup = BeautifulSoup(text, 'html.parser')
        field_values = soup.find_all('input', {'name': 'FV'})
        field_value = field_values[0]['value'] if field_values != [] else ''
        print(_id, field_value)
        conn.products_part.update({'_id': _id}, {'$set': {'crawled': 1, 'field_value': field_value}})


#  下载excel
def download_product():
    # 'https://www.digikey.cn/product-search/download.csv?FV=ffe003b7&quantity=0&ColumnSort=0&page=1&pageSize=500'
    products_part = conn.products_part.find({"crawled": 1, "downloaded": 0}).limit(1)
    for product_part in products_part:
        _id = product_part['_id']
        count = product_part['count']
        filed_value = product_part['field_value']
        product_part = product_part['part']
        count = int(count) if not math.isnan(count) else 0
        # print(count)
        max_page = math.ceil(int(count) / 500)
        pages = []
        for i in range(0, max_page, 1):
            pages.append(i)

        print(filed_value, max_page)
        # 根据页数下载文件
        for page in pages:
            url = 'https://www.digikey.cn/product-search/download.csv?FV=' + filed_value + \
                  '&quantity=0&ColumnSort=0&page=' + str(page + 1) + '&pageSize=500'
            excel_name = product_part + ' page' + str(page + 1)
            print(filed_value, url, int(count), max_page, excel_name)
            save_excel(url, excel_name)
        conn.products_part.update({'_id': _id}, {'$set': {'downloaded': 1}})


# 存储excel
def save_excel(url, name):
    root = 'Document/'
    name = re.sub('[\/:*?"<>|]', '-', name)  # 去掉非法字符
    path = root + name + '.csv'

    if not os.path.exists(path):
        html = get_html_text(url)
        with open(path, "wb") as f:
            # print(html)
            print(path)
            if html != 'Error!':
                f.write(html)
            f.close()


def main():
    # # 获取products part
    # url = "https://www.digikey.cn/products/zh"
    # html = get_html_text(url)
    # parse_products_part_html(html)

    # # 获取 filed value
    # while True:
    #     get_product_field_value()
    #     # random_sleep = random.uniform(2.0, 5.0)
    #     # time.sleep(random_sleep)

    # 下载产品信息
    while True:
        download_product()
        random_sleep = random.uniform(1.0, 2.0)
        time.sleep(random_sleep)


if __name__ == '__main__':
    main()
