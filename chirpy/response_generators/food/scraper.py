# from bs4 import BeautifulSoup
import requests
import re
from collections import defaultdict
import json
from lxml.html.soupparser import fromstring
import lxml.etree
import urllib
from collections import defaultdict
import time
import inflect

engine = inflect.engine()

out = defaultdict(dict)

r = requests.get('https://en.wikipedia.org/wiki/Lists_of_foods')
base_list = fromstring(r.content)

BASE_URL = 'https://en.wikipedia.org'

def make_singular(text):
    proposed_singular = engine.singular_noun(text)
    if proposed_singular: return proposed_singular
    return text

def get_views_for_article(article):
    url = f'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/monthly/2020010100/2020013100'
    try:
        out = json.loads(requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).content)
    except requests.exceptions.ConnectionError:
        return 0
    try:
        return out['items'][0]['views']
    except KeyError as e:
        # print(out)
        return 0



def split(text):
    try:
        data = [x.strip().lower() for x in re.split(',|;|\sand\s|\sor\s|\swith\s|\ssometimes\s|\soften\s|\.|usually|\(|\)|/', text)]
        data = [x for x in data if x]
        return data
    except Exception as e:
        print(text)
        raise e

def get_data_for_link(url, type, get_infobox=[]):
    #get pageviews
    # url = (f'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/' +
    #       'all-agents/Albert_Einstein/daily/2020010100/2020010200')
    # out = requests.get(url, headers={'headers': 'User-Agent: Testing123/0.0 (https://example.org/cool-tool/; cool-tool@example.org) used-base-library/0.0'})
    # print(out)
    views = get_views_for_article(url.replace('/wiki/', ''))
    # print(url, views)
    if views < 10000: return None, None
    try:
        out = requests.get(BASE_URL + url)
    except requests.exceptions.ConnectionError:
        try:
            time.sleep(5)
            out = requests.get(BASE_URL + url)
        except requests.exceptions.ConnectionError:
            return None, None
    content = out.content.decode('utf-8')
    root = fromstring(content)
    # if get_ingredients:
    #     ingredients = root.xpath("//td[@class='ingredient']") # /tbody/tr/td[@class="ingredient"]
    #     if not ingredients and get_ingredients: return None, None
    #     ingredients_text = lxml.etree.tostring(ingredients[0], method="text", encoding='utf-8').decode('utf-8')
    #
    #     print(url, ingredients, views)
    #     time.sleep(0.25)
    out = {}
    for elem in get_infobox:
        elem_data = root.xpath(f"//tr[th[contains(text(), '{elem}')]]/td")
        if len(elem_data) == 0: continue
        elem_data = lxml.etree.tostring(elem_data[0], method="text", encoding='utf-8').decode('utf-8')
        elem_data = re.sub('\[.*\]', '', elem_data)
        elem_data = re.sub('\(.*\)', '', elem_data)

        if elem == 'Main ingredients':
            elem_data = split(elem_data)
        if elem_data is None: continue
        elem_key = elem.lower().split(' ')[-1]
        out[elem_key] = elem_data
    # parse for Xth century
    if type not in ('edible seed', 'citrus fruit'):
        body = root.xpath("//div[@id='bodyContent']")[0]
        body = re.sub('<!--[\s\S]*?-->', '', lxml.etree.tostring(body).decode('utf-8'))
        proposed_year = re.search(r'\s((?:\d|1[1-9])(?:st|nd|rd|th)\scentury)', body)
        if proposed_year is None: proposed_year = re.search(r'(?:invented|created|discovered)[^.,]*\s(1?\d\d\ds?)\b', body)
        if proposed_year is None: proposed_year = re.search(r'\s(1?\d\d\ds)\b', body)
        if proposed_year is None: proposed_year = re.search(r'\s(1[1-8]\d\d)\b', body)
        if proposed_year is not None: out['year'] = proposed_year.group(1)

    return out, views
    # assert False

items = {}

BANNED = ['bean-to-bar', 'kosher', 'country', 'antioxidant', 'animal', 'topic', 'dried', 'culinary', 'garden', 'plants', 'cultivars', 'topics', 'antioxidants', 'Designations', 'accompaniments', 'Indian', 'brand', 'manufacturer', 'origin', 'edible']

categories = set()

links = [x.get('href') for x in base_list.xpath("//a[contains(@href, '/wiki/List_of_')]")]
print("Skipping:", [l for l in links if any(x in l for x in BANNED)])
links = [l for l in links if not any(x in l for x in BANNED)]
try:
    for link in links: # ["/wiki/List_of_desserts", "/wiki/List_of_cheeses", "/wiki/List_of_breads", "/wiki/List_of_desserts", "/wiki/List_of_noodles"]: # "/wiki/List_of_desserts",
        if '#' in link: continue
        title = urllib.parse.unquote(link.replace('/wiki/List_of_', ''))
        title = title.replace('_', ' ')

        title = title.split()

        # continue
        title[-1] = make_singular(title[-1])

        title = ' '.join(title)
        if 'pie' in title: title = 'pie'
        if 'snack food' in title: title = 'snack'
        if title[0].isupper(): continue
        url = BASE_URL + link
        r2 = requests.get(url)
        content2 = r2.content.decode('utf-8')
        root = fromstring(content2)



        def add_link(link):
            href = link.get('href')
            if 'index' in href: return
            if 'beer in' in href.lower(): return
            if 'alexandria' in href.lower(): return
            if ':' in href: return
            if 'List' in href: return
            if '#' in href: return
            data, views = get_data_for_link(link.get('href'), type=title, get_infobox=['Texture', 'Main ingredients', 'Place of origin'])
            if data is None: return
            food_name = urllib.parse.unquote(link.get('href').replace('/wiki/', '').replace('_', ' ')).lower()
            food_name = re.sub('\(.*\)', '', food_name)
            items[food_name] = {
                'type': title,
                'views': views
            }
            categories.add(title)
            items[food_name].update(data)
            print('Item:', food_name, items[food_name])
            # time.sleep(0.1)

        for link in root.xpath("//div[@class='div-col']/ul/li/a"): #
            add_link(link)

        for link in root.xpath("//table[contains(@class, 'wikitable')]/tbody/tr/td[1]/a[not(@class)]"): #
            add_link(link)





except KeyboardInterrupt:
    print("Stopping.")


ingredients_counts = defaultdict(int)
for food, food_dict in items.items():
    if 'ingredients' in food_dict:
        for ingredient in food_dict['ingredients']:
            ingredients_counts[ingredient] += 1
print(ingredients_counts)


out = {
    'foods': items,
    'ingredients': ingredients_counts,
    'categories': list(categories),
}

with open('scraped_data6.json', 'w') as outfile:
    json.dump(out, outfile, sort_keys=True, indent=4)

# for url in urls:
