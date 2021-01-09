import os
import re
import bz2
import json
import argparse
import unicodedata
import sys
import mwparserfromhell as mw
import xml.etree.ElementTree as ET

from shutil import rmtree
from typing import List
from collections import Counter
from operator import add
from ast import literal_eval
from pyspark import SparkContext, SparkConf, StorageLevel

HEADING = r'\s*=+([^=]*)=+\s*'
CATEGORY = r'\[\[Category:([^\]]+)\]\]'
NAMESPACE = r'\[\[(User|Wikipedia|WP|Project|WT|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category|Talk):.*?\]\]'
NAMESPACE_TALK = r'\[\[(User|Wikipedia|WP|Project|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category) talk:.*?\]\]'
NAMESPACE_TITLE = r'(User|Wikipedia|WP|Project|WT|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category|Talk):.*'
NAMESPACE_TALK_TITLE = r'(User|Wikipedia|WP|Project|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category) talk:.*'
TITLE_SECTION = r'http:\/\/en\.wikipedia\.org\/wiki\/([^#]+)#?(.*)'
SPECIAL_RE = re.compile('^Special:.*')
PUNC_TABLE = dict.fromkeys(i for i in range(sys.maxunicode) if unicodedata.category(chr(i)).startswith('P'))

#####################
# Utility Functions #
#####################

def remove_punc(text: str, keep: List[str] = [], replace_with_space: List[str] = ['-', '/']):
    """
    Removes all Unicode punctuation (this is more extensive than string.punctuation) from text.
    Most punctuation is replaced by nothing, but those listed in replace_with_space are replaced by space.

    Solution from here: https://stackoverflow.com/questions/11066400/remove-punctuation-from-unicode-formatted-strings/11066687#11066687

    Inputs:
        keep: list of strings. Punctuation you do NOT want to remove.
        replace_with_space: list of strings. Punctuation you want to replace with a space (rather than nothing).
    """
    punc_table = {codepoint: replace_str for codepoint, replace_str in PUNC_TABLE.items() if chr(codepoint) not in keep}
    punc_table = {codepoint: replace_str if chr(codepoint) not in replace_with_space else ' ' for codepoint, replace_str
                  in punc_table.items()}
    text = text.translate(punc_table)
    text = " ".join(text.split()).strip()  # Remove any double-whitespace
    return text

def process_seek(tup):
    dump_path, seek, seek_len = tup
    with open(dump_path, 'rb') as f:
        f.seek(seek)
        doc = f.read(seek_len)
        xml = bz2.decompress(doc).decode('utf-8').replace('</mediawiki>', '')
        tree = ET.fromstring('<data>\n' + xml + '\n</data>')
        pages = []
        for page in tree:
            current_page = {}
            for elem in page:
                if elem.tag == 'title':
                    current_page['title'] = elem.text
                if elem.tag == 'id':
                    current_page['id'] = elem.text
                if elem.tag == 'redirect':
                    current_page['redirect'] = elem.attrib
                if elem.tag == 'revision':
                    current_page['text'] = next(child for child in elem if child.tag == 'text').text
            pages.append(current_page)
    return pages

def parse_sections(page, wiki):
    parsed_sections = []
    title_stack = []
    sections = wiki.get_sections(flat=True, include_headings=True)
    i = -1
    for section in sections:
        section_no_heading = [node for node in section.nodes if type(node) != mw.nodes.heading.Heading]
        section_plain = mw.wikicode.Wikicode(section_no_heading).strip_code().strip()
        headings = section.filter_headings()
        if len(headings) == 0:
            heading_level, title = 0, ''
        else:
            heading = headings[0]
            heading_level = (heading.count('=') // 2) - 1
            title = mw.wikicode.Wikicode.strip_code(headings[0].title).strip()
        if len(title_stack) < heading_level:
            title_stack.append(title)
        else:
            title_stack = title_stack[:heading_level-1] + [title]
        if len(section_plain) == 0:
            continue
        i += 1
        parsed_sections.append(json.dumps({
            'doc_title' : page['title'],
            'doc_id' : page['id'],
            'text': section_plain,
            'title': title,
            'title_keyword': title,
            'title_stack' : list(title_stack),
            'order': i,
            'wiki_links': [str(link.title) for link in section.filter_wikilinks()]
        }))
    return parsed_sections

def parse_doc(page):
    # First add all basic 
    article = {
        'doc_title' : page['title'],
        'doc_id' : page['id'],
        'categories' : list(re.findall(CATEGORY, page['text'])),
        'redirects' : [],
        'pageview': 0,
        'overview_section' : '',
        'full_text' : '',
        'linkable_span' : [],
        'linkable_span_info': []
    }
    text = re.sub(r'\*.*?\n', '', page['text']) # remove lists
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL) # remove tables
    text = re.sub(NAMESPACE, '', text) # remove name spaces
    text = re.sub(NAMESPACE_TALK, '', text) # remove name spaces talk
    text = re.sub(CATEGORY, '', text) # remove category links
    wiki = mw.parse(text)
    no_ref_nodes = [node for node in wiki.nodes if type(node) != mw.nodes.tag.Tag or node.tag != 'ref']
    wiki_cleaned = mw.wikicode.Wikicode(no_ref_nodes)
    sections = wiki_cleaned.get_sections(flat=True, include_headings=True)
    for section in sections:
        if section.filter_headings() == []:
            article['overview_section'] = section.strip_code().strip()
    article['full_text'] = wiki_cleaned.strip_code().strip()
    links = wiki.filter_wikilinks()
    links = [(link.title.strip_code().strip(), link.text.strip_code().strip() if link.text is not None else link.title.strip_code().strip()) for link in links]
    links = [(title.replace('_', ' '), remove_punc(text.lower().strip(), keep=["'"])) for title, text in links]
    return (page['title'], json.dumps(article), links, parse_sections(page, wiki_cleaned))

def safe_parse_doc(page):
    try:
        return parse_doc(page)
    except:
        print(f"Error parsing page: {page['title']}")
        raise RuntimeError()

def add_redirects(tup):
    title, (article, redirects) = tup
    article['redirects'] = redirects if redirects is not None else []
    return title, article
    
def add_pageviews(tup):
    title, (article, pageview) = tup
    article['pageview'] = pageview if pageview is not None else 0
    return title, article

def add_entities(tup):
    title, (article, span_infos) = tup
    article['linkable_span_info'] = span_infos if span_infos else []
    article['linkable_span'] = [span for span, _ in span_infos] if span_infos else []
    return title, article


def is_valid(super_category):
    return 'mainsnak' in super_category and \
        'datavalue' in super_category['mainsnak'] and \
        super_category['mainsnak']['snaktype'] == 'value' and \
        'value' in super_category['mainsnak']['datavalue'] and \
        'id' in super_category['mainsnak']['datavalue']['value']

def parse_wikidata_entity(entity):
    instance_of, subclass_of, occupation = [], [], []
    if 'claims' in entity and 'P31' in entity['claims']:
        instance_of = [super_category['mainsnak']['datavalue']['value']['id'] for super_category in entity['claims']['P31'] if is_valid(super_category)]
    if 'claims' in entity and 'P279' in entity['claims']:
        subclass_of = [super_category['mainsnak']['datavalue']['value']['id'] for super_category in entity['claims']['P279'] if is_valid(super_category)]
    if 'claims' in entity and 'P106' in entity['claims']:
        occupation = [super_category['mainsnak']['datavalue']['value']['id'] for super_category in entity['claims']['P106'] if is_valid(super_category)]
    return (entity['id'], {
        'id': entity['id'],
        'name': entity['labels']['en']['value'],
        'wiki_title': entity['sitelinks']['enwiki']['title'] if 'sitelinks' in entity and 'enwiki' in entity['sitelinks'] else None,
        'instance_of': instance_of,
        'subclass_of': subclass_of,
        'occupation' : occupation
    })

def update_categories(tup):
    entity_id, (old_info, new_categories) = tup
    max_dist, existing_categories, old_unprocessed = old_info
    unprocessed_categories = []
    if new_categories is None:
        return entity_id, old_info
    for category in old_unprocessed:
        existing_categories[category] = max_dist
    for category in new_categories:
        if category not in existing_categories:
            unprocessed_categories.append(category)
    return entity_id, (max_dist + 1, existing_categories, unprocessed_categories)

def add_wikidata_categories(tup):
    _, (article, category_levels) = tup
    article.update(category_levels)
    return article

##########
# Stages #
##########
def stage0(args):
    """
    This mega stage parses everything
    """
    print(f'>  Processing Wiki dump at {args.dump_path}')
    index_path = args.dump_path.replace('.xml', '-index.txt')
    lines = sc.textFile(index_path).repartition(256)
    all_seeks = lines.map(lambda line: int(line.split(':', maxsplit=1)[0])).distinct().sortBy(lambda x:x).collect()
    all_seeks_tup = [(args.dump_path, all_seeks[i], all_seeks[i + 1] - all_seeks[i]) for i in range(len(all_seeks) - 1)] + [(args.dump_path, all_seeks[-1], -1)]
    all_seeks_tup = sc.parallelize(all_seeks_tup).repartition(2048)
    processed_rdd = all_seeks_tup.flatMap(process_seek)
    resolved_path = args.dump_path.replace('.xml', '-resolved.json')
    processed_rdd\
        .map(lambda page: (page['title'], page['title'] if 'redirect' not in page else page['redirect']['title']))\
        .saveAsTextFile(resolved_path, 'org.apache.hadoop.io.compress.BZip2Codec')
    parsed_path = args.dump_path.replace('.xml', '-parsed.json')
    processed_rdd\
        .filter(lambda page: 'redirect' not in page and page['text'] is not None)\
        .map(safe_parse_doc)\
        .saveAsTextFile(parsed_path, 'org.apache.hadoop.io.compress.BZip2Codec')

def stage1(args):
    resolved_path = args.dump_path.replace('.xml', '-resolved.json')
    parsed_path = args.dump_path.replace('.xml', '-parsed.json')
    resolved_rdd = sc.textFile(resolved_path).map(lambda s: literal_eval(s))
    parsed_rdd = sc.textFile(parsed_path).map(lambda s: literal_eval(s))
    # redirects : [(resolved_title, [titles, ...])]
    redirects = resolved_rdd\
        .map(lambda tup: (tup[1], [tup[0]]))\
        .reduceByKey(add)

    # pageviews : [(title, pageview_int)]
    pageview_rdd = sc.textFile(args.pageview_path)
    pageviews = pageview_rdd\
        .map(lambda l: l.split(' '))\
        .filter(lambda row: len(row) == 3)\
        .filter(lambda row: row[0] == 'en.z')\
        .filter(lambda row: row[1] is not None and SPECIAL_RE.fullmatch(row[1]) is None)\
        .map(lambda row: (row[1].replace('_', ' '), int(row[2]))).repartition(32)

    # resolved_pageviews : [(resolved_title, pageview_int)]
    resolved_pageviews = resolved_rdd.leftOuterJoin(pageviews)\
        .map(lambda tup: (tup[1][0], tup[1][1]))\
        .reduceByKey(lambda a, b: (a and b and a + b) or (a or b))

    # entities : [(resolve_title, text)]
    entities = parsed_rdd\
        .map(lambda o: o[2])\
        .flatMap(lambda x: x)\
        .map(lambda tup: (tup[0], [tup[1]]))\
        .reduceByKey(add, 512)\
        .map(lambda tup: (tup[0], list(Counter(tup[1]).most_common(256))))

    articles_path = args.dump_path.replace('.xml', '-articles.json')
    parsed_rdd\
        .filter(lambda tup: not re.match(NAMESPACE_TITLE, tup[0]))\
        .filter(lambda tup: not re.match(NAMESPACE_TALK_TITLE, tup[0]))\
        .map(lambda tup: (tup[0], json.loads(tup[1])))\
        .leftOuterJoin(redirects)\
        .map(add_redirects)\
        .leftOuterJoin(resolved_pageviews)\
        .map(add_pageviews)\
        .leftOuterJoin(entities)\
        .map(add_entities).repartition(1024)\
        .saveAsTextFile(articles_path, 'org.apache.hadoop.io.compress.BZip2Codec')
    
    # sections_path = args.dump_path.replace('.xml', '-sections.json')
    # parsed_rdd\
    #     .filter(lambda tup: not re.match(NAMESPACE_TITLE, tup[0]))\
    #     .filter(lambda tup: not re.match(NAMESPACE_TALK_TITLE, tup[0]))\
    #     .flatMap(lambda tup: tup[3]).repartition(1024)\
    #     .map(lambda s: json.loads(s))\
    #     .saveAsTextFile(sections_path, 'org.apache.hadoop.io.compress.BZip2Codec')\


def stage2(args):
    processed_path = args.wikidata_path.replace('.json', '-processed.json')
    sc.textFile(args.wikidata_path).filter(lambda line: line != '[' and line != ']')\
        .map(lambda line: line[:-1] if line[-1] == ',' else line)\
        .map(lambda line: json.loads(line))\
        .filter(lambda entity: 'labels' in entity and 'en' in entity['labels'] and 'value' in entity['labels']['en'])\
        .map(parse_wikidata_entity)\
        .saveAsTextFile(processed_path, 'org.apache.hadoop.io.compress.BZip2Codec')

def stage3(args):
    processed_path = args.wikidata_path.replace('.json', '-processed.json')
    processed_rdd = sc.textFile(processed_path).map(lambda s: literal_eval(s))
    processed_rdd.persist(StorageLevel(True, True, False, False, 1))

    ## Restore last checkpoint
    start_level = 0
    for i in range(args.level):
        expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-level{}.txt'.format(i))
        if os.path.exists(expanded_path):
            start_level = i + 1
    if start_level > 0:
        print(f'Starting level {start_level} > 0, restoring previous checkpoint')
        expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-level{}.txt'.format(start_level - 1))
        all_categories = sc.textFile(expanded_path).map(literal_eval)
    else:
        all_categories = processed_rdd\
            .filter(lambda tup: tup[1]['wiki_title'] is not None)\
            .map(lambda tup: (tup[0], (0, {}, tup[1]['instance_of'] + tup[1]['subclass_of'] + tup[1]['occupation'])))

    for i in range(start_level, args.level):
        next_level_categories = all_categories\
            .filter(lambda tup: tup[1][-1] != [])\
            .flatMap(lambda tup: [(category, tup[0]) for category in tup[1][-1]])\
            .join(processed_rdd)\
            .map(lambda tup: (tup[1][0], tup[1][1]['subclass_of']))\
            .reduceByKey(add, 512)
        next_all_categories = all_categories.leftOuterJoin(next_level_categories, 512)\
            .map(update_categories)
        next_all_categories.persist(StorageLevel(True, True, False, False, 1))
        all_categories.unpersist()
        all_categories = next_all_categories
        unfinished_entities = all_categories.filter(lambda tup: tup[1][-1] != []).count()
        print('After {} iterations, there are still {} entities that needs to be expanded'.format(i + 1, unfinished_entities))
        expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-level{}.txt'.format(i))
        print('Persisting it onto disk with file name {}'.format(expanded_path))
        all_categories.saveAsTextFile(expanded_path, 'org.apache.hadoop.io.compress.BZip2Codec')
        if i > 0:
            old_expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-level{}.txt'.format(i - 1))
            print(f'Removing old directory {old_expanded_path}')
            rmtree(old_expanded_path)
        if unfinished_entities == 0:
            break

def stage4(args):
    processed_path = args.wikidata_path.replace('.json', '-processed.json')
    names_rdd = sc.textFile(processed_path).map(lambda s: literal_eval(s))\
        .map(lambda tup: (tup[0], (tup[1]['name'], tup[1]['wiki_title']))) # (id, (name, wiki_title))
    names_rdd.persist()
    expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-level{}.txt'.format(args.level - 1))
    expanded_rdd = sc.textFile(expanded_path).map(lambda s: literal_eval(s)) # (id, (max_dist, cat_dict, unprocessed))
    wikidata_categories_rdd = expanded_rdd.flatMap(lambda tup: [(category_id, (tup[0], level)) for category_id, level in tup[1][1].items()])\
        .join(names_rdd)\
        .map(lambda tup: tup[1])\
        .map(lambda tup: (tup[0][0], [(tup[1][0], tup[0][1])]))\
        .reduceByKey(add, 512)\
        .join(names_rdd)\
        .filter(lambda tup: tup[1][1][1] is not None)\
        .map(lambda tup: (tup[1][1][1], \
            {'wikidata_id': tup[0],
             'wikidata_categories_all': [category for category, _ in tup[1][0]],
             'wikidata_categories_info' : json.dumps(dict(tup[1][0]))}))
    final_expanded_path = args.wikidata_path.replace('.json.bz2', '-expanded-named.txt')
    wikidata_categories_rdd.saveAsTextFile(final_expanded_path, 'org.apache.hadoop.io.compress.BZip2Codec')

def stage5(args):
    merge_dicts = lambda tup: (tup[0], (tup[1][0].update(tup[1][1]) or tup[1][0]) if tup[1][1] is not None else tup[1][0])
    final_updated_path = args.wikidata_path.replace('.json.bz2', '-expanded-named.txt')
    articles_path = args.dump_path.replace('.xml', '-articles.json')
    final_upload = articles_path.replace('-articles.json', '-wikidata-integrated.json')
    articles_rdd = sc.textFile(articles_path).map(lambda s: literal_eval(s))
    wikidata_categories_rdd = sc.textFile(final_updated_path).map(lambda s: literal_eval(s))
    articles_rdd.leftOuterJoin(wikidata_categories_rdd, 1024)\
        .map(merge_dicts)\
        .saveAsTextFile(final_upload, 'org.apache.hadoop.io.compress.BZip2Codec')

if __name__ == "__main__":
    conf = SparkConf().setAppName('wiki-parse').set('spark.driver.maxResultSize', 0)
    sc = SparkContext(conf=conf)

    parser = argparse.ArgumentParser(description='Fully process a Wikipedia Dump')
    parser.add_argument('dump_path', type=str, help='Fully Qualified path of the wikipedia dump')
    parser.add_argument('pageview_path', type=str, help='Fully Qualified path of the pageview dump')
    parser.add_argument('wikidata_path', type=str, help='Fully Qualified path of the wikidata dump')
    parser.add_argument('level', type=int, default=24, help='The expansion level of Wikidata types')
    args = parser.parse_args()
    stages = [stage0, stage1, stage2, stage3, stage4, stage5]
    for i in range(len(stages)):
        stages[i](args)