import argparse
from elasticsearch import Elasticsearch

def define_articles(es, index_name):
    if es.indices.exists(index_name):
        es.indices.delete(index_name)
    es.indices.create(index_name, body=\
    {
        'mappings':
        {
            'properties': {
                'doc_title' : {'type': 'keyword'},
                'doc_id' : {'type': 'keyword'},
                'categories': {'type': 'keyword'},
                'redirects': {'type': 'keyword'},
                'pageview': {'type': 'long'},
                'overview_section': {'type': 'text'},
                'full_text': {'type': 'text'},
                'linkable_span': {'type': 'keyword'},
                'linkable_span_info': {'type': 'text'},
                'wikidata_id': {'type': 'keyword'},
                'wikidata_categories_all' : {'type': 'keyword'},
                'wikidata_categories_info' : {'type': 'text'}
            }
        }
    })

def define_sections(es, index_name):
    if es.indices.exists(index_name):
        es.indices.delete(index_name)
    es.indices.create(index_name, body=\
    {
        'mappings':
        {
            'properties': {
                'doc_title': {'type': 'keyword'},
                'doc_id': {'type': 'keyword'},
                'text': {'type': 'text'},
                'title': {'type': 'text'},
                'title_keyword': {'type': 'keyword'},
                'title_stack': {'type': 'text'},
                'order': {'type': 'integer'},
                'wiki_links': {'type': 'keyword'}
            }
        }
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fully process a Wikipedia Dump')
    parser.add_argument('-d', '--domain', type=str, help='The host domain name of the ES index')
    parser.add_argument('-p', '--port', type=str, help='The port of the ES index')
    parser.add_argument('-U', '--username', type=str, help='The username of the ES index')
    parser.add_argument('-P', '--password', type=str, help='The password of the ES index')
    parser.add_argument('-s', '--scheme', type=str, default='http', help='The scheme to use for the connection')
    args = parser.parse_args()
    host, port, username, password, scheme = args.domain, args.port, args.username, args.password, args.scheme
    es = Elasticsearch([{'host': host, 'port': port}], http_auth=(username, password), timeout=99999)
    es = Elasticsearch([{'host': host, 'port': port}], http_auth=(username, password), scheme=scheme, timeout=99999)
    define_articles(es, 'enwiki-20201201-articles')
    define_sections(es, 'enwiki-20201201-sections')