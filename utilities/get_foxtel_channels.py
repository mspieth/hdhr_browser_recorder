#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

import pprint
import lxml.html
from urllib import request

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3445.2 Safari/537.36'

def get_page(url):
    return request.urlopen(request.Request(url,  data=None, headers={'User-Agent': USER_AGENT}))

def read_document(response):
    return response.read()

def extract_data(document):
    # Generate document tree
    tree = lxml.html.fromstring(document)
    # Select tr with a th and td descendant from table
    # elements = tree.xpath('//div[@id="lia-message-body-content"]/table/tbody/tr[th and td]')
    elements = tree.xpath('//div[@class="lia-message-body-content"]/table/tbody/tr')
    # Extract data
    result = {}
    # header = []
    count = 0
    for element in elements:
        count += 1
        if count == 1:
            continue
        if count == 2:
            # items = element.xpath('td')
            # for item in items:
            #     # print(f"header {item.text_content().strip()}")
            #     header.append(item.text_content().strip())
            continue

        items = element.xpath('td')
        text = items[0].text_content().strip()
        if not text:
            continue
        if '-' not in text:
            continue
        number, name = text.split('-')
        numbers = number.strip().split(' & ')
        name = name.strip()
        # print(f"item {item.text_content().strip()}")
        for number in numbers:
            entry = {
                'Number': number,
                'Name': name
            }
            result.update({number: name})
    return result


def extract_data_2(document):
    # Generate document tree
    tree = lxml.html.fromstring(document)
    # pprint.pprint(document)
    # Select tr with a th and td descendant from table
    # elements = tree.xpath('//div[@id="lia-message-body-content"]/table/tbody/tr[th and td]')
    elements = tree.xpath('//div[@class="epg-channel-callout"]')
    # elements = tree.xpath('//a[@class="epg-channel-callout"]/p[@class="epg_channel-name"] and p[@class="epg-channel-callout-number"]')
    # Extract data
    result = {}
    # header = []
    count = 0
    for element in elements:
        name, number = element.iterchildren()
        result.update({name.text_content(): {'number': number.text_content(), 'name': name.text_content()}})
    return result

def filter(data):
    names = data.keys()
    for channel_name in names:
        if channel_name + " HD" in names:
            name = channel_name
            data[name].update({'hd_number': data[name+' HD']['number']})
            data[name + ' HD'].update({'sd_number': data[name]['number']})
            print(f"hd equiv {channel_name}")

    return data


def main():
    mode = True
    if mode:
        response = get_page('http://www.foxtel.com.au/tv-guide/grid')
        document = read_document(response)
        data = extract_data_2(document)
        data = filter(data)
    else:
        response = get_page('https://community.foxtel.com.au/t5/Entertainment/Foxtel-Channel-List/td-p/170370')
        document = read_document(response)
        data = extract_data(document)
    pprint.pprint(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())