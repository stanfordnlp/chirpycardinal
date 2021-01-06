import re
import json
import argparse

from ast import literal_eval
from pyspark import SparkContext, SparkConf
from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch


NAMESPACE_TITLE = r'(User|Wikipedia|WP|Project|WT|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category|Talk):.*'
NAMESPACE_TALK_TITLE = r'(User|Wikipedia|WP|Project|File|Image|MediaWiki|Template|Help|Portal|Book|Draft|TimedText|Module|Category) talk:.*'

conf = SparkConf().setAppName('wiki-upload').set('spark.driver.maxResultSize', 0)
sc = SparkContext(conf=conf)

def upload_partition(partition):
    es = Elasticsearch([{'host': HOST, 'port': PORT}], http_auth=(USERNAME, PASSWORD), scheme=SCHEME, timeout=99999)
    actions = ({
        '_index': index,
        '_type': '_doc',
        '_source' : article
    } for index, article in partition)
    bulk(es, actions)

if __name__ == "__main__":
    conf = SparkConf().setAppName('wiki-parse').set('spark.driver.maxResultSize', 0)
    sc = SparkContext(conf=conf)

    parser = argparse.ArgumentParser(description='Fully process a Wikipedia Dump')
    parser.add_argument('sections_path', type=str, help='Fully Qualified path of the proessed *-sections.json.bz2 file')
    parser.add_argument('articles_path', type=str, help='Fully Qualified path of the *-integrated.json.bz2 file')
    parser.add_argument('-d', '--domain', type=str, help='The host domain name of the ES index')
    parser.add_argument('-p', '--port', type=str, help='The port of the ES index')
    parser.add_argument('-U', '--username', type=str, help='The username of the ES index')
    parser.add_argument('-P', '--password', type=str, help='The password of the ES index')
    parser.add_argument('-s', '--scheme', type=str, default='http', help='The scheme to use for the connection')
    args = parser.parse_args()
    HOST, PORT, USERNAME, PASSWORD, SCHEME = args.domain, args.port, args.username, args.password, args.scheme
    sc.textFile(args.sections_path)\
        .map(lambda s: ('enwiki-20201201-sections', literal_eval(s)))\
        .foreachPartition(upload_partition)
    sc.textFile(args.articles_path)\
        .map(lambda s: literal_eval(s))\
        .map(lambda tup: ('enwiki-20201201-articles', tup[1]))\
        .foreachPartition(upload_partition)