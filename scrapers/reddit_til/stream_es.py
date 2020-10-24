import praw
import re
import os
from typing import Optional, Tuple, Dict
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.helpers import bulk
from chirpy.core.util import get_es_host

from requests_aws4auth import AWS4Auth

host = get_es_host("wiki")
region = 'us-east-1'
service = 'es'
# credentials = boto3.Session().get_credentials()
# awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
# es = Elasticsearch(
#     hosts = [{'host': host, 'port': 443}],
#     http_auth = awsauth,
#     use_ssl = True,
#     verify_certs = True,
#     connection_class = RequestsHttpConnection,
#     timeout=99999)

TIL_RE = r'(til|today i learned),? (that )?((.*)+)'
URL_RE = r'(https://en.wikipedia.org/wiki/)([^#]+)(#(.*))?'

client_id = os.environ.get('REDDIT_CLIENT_ID')
client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
reddit = praw.Reddit(client_id=client_id,
    client_secret=client_secret,
    user_agent='python')

submissions = [submission for submission in reddit.subreddit("TodayILearned").top('day')]
wiki_tagged_submissions = [submission for submission in submissions if 'en.wikipedia.org' in submission.url]

def parse_submission(submission) -> Optional[Tuple[str, int, str, str]]:
    url_matched = re.match(URL_RE, submission.url)
    if url_matched is None:
        return None
    text = submission.title
    doc_title = url_matched.group(2)
    section_title = url_matched.group(4)
    score = submission.score
    return doc_title, score, section_title if section_title is not None else '', text

def format_into_dict(tup: Tuple[str, int, str, str]) -> Tuple[str, Dict]:
    return 'til', {
        'doc_title': tup[0].replace('_', ' '),
        'score' : tup[1],
        'section_title': tup[2].replace('_', ' '),
        'til' : tup[3]
    }

def upload_partition(partition):
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    es = Elasticsearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection,
        timeout=99999)
    actions = ({
        '_index': index,
        '_type': '_doc',
        '_source' : article
    } for index, article in partition)
    bulk(es, actions)

parsed_submissions = list(map(parse_submission, wiki_tagged_submissions))
parsed_submissions = [format_into_dict(submission) for submission in parsed_submissions if submission is not None]
upload_partition(parsed_submissions)

