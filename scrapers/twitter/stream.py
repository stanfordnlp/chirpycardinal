import os
import re
import time
import boto3
import tweepy
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from chirpy.core import get_es_host

CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')
LIKE_REGEX = r'i (love|like|admire|adore) ([\w ]+) because ([^.!?;]+)'
DISLIKE_REGEX = r'i (hate|don\'t like|dislike) ([\w ]+) because ([^.!?;]+)'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

host = get_es_host("opinion_twitter") # the Amazon ES domain, with https://
region = 'us-east-1' # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection,
    timeout=2,
)

def upload_to_es(entity, reason, attitude, sentiment, tweet_id, original_text):
    data = {
        'entity': entity,
        'entity_keyword': entity,
        'reason': reason,
        'attitude': attitude,
        'sentiment': sentiment,
        'tweet_id': tweet_id,
        'original_text': original_text
    }
    es.index(index='opinion', body=data)

class OpinionStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        try:
            text = status.text.lower()
            tweet_id = status.id_str
            if status.truncated:
                text = status.extended_tweet['full_text'].lower()
            like = re.search(LIKE_REGEX, text)
            dislike = re.search(DISLIKE_REGEX, text)
            if like is not None:
                attitude, entity, reason = like.groups()
                sentiment = 'positive'
            elif dislike is not None:
                attitude, entity, reason = dislike.groups()
                sentiment = 'negative'
            else:
                return
            upload_to_es(entity, reason, attitude, sentiment, tweet_id, text)
            print('uploaded [{}] to elastic search'.format(text))
        except:
            pass

# class FakeStatus():
#     def __init__(self, text):
#         self.text = text
#         self.truncated = False

# fake_status = FakeStatus('i love vague lyrics because the emotions or meaning derived from them is very individualized')
# listener.on_status(fake_status)

while True:
    try:
        like_stream = tweepy.Stream(auth=api.auth, listener=OpinionStreamListener(), tweet_mode='extended')
        like_stream.filter(track=['i like because', 'i love because', 'i admire because', 'i adore because', 'i don\'t like because', 'i hate because', 'i dislike because'])
    except:
        print('exception occurred. Sleeping for 5 seconds')
        time.sleep(5)