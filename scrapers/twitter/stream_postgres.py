import re
import os
import sys
import json
import time
import boto3
import tweepy
import psycopg2
#from chirpy.core.util import get_es_host

#host = get_es_host("postgres")
host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT')
database = 'twitter_opinions'
user = 'postgres@chirpy-postgres'
password = os.environ.get('POSTGRES_PW')

CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')
LIKE_REGEX = r'i (love|like|admire|adore) ([\w ]+) because ([^.!?;\n]+)'
DISLIKE_REGEX = r'i (hate|don\'t like|dislike) ([\w ]+) because ([^.!?;\n]+)'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

def insert(entity, reason, attitude, sentiment, status=None):
    cur = conn.cursor()
    if status:
        insert = """
        insert into opinions (entity, reason, attitude, sentiment, creation_date_time, status)
        values (%s, %s, %s, %s, current_timestamp, %s)
        """
        result = cur.execute(insert,(entity, reason, attitude, sentiment, status))
    else:
        insert = """
        insert into opinions (entity, reason, attitude, sentiment, creation_date_time, status)
        values (%s, %s, %s, %s, current_timestamp, null)
        """
        result = cur.execute(insert,(entity, reason, attitude, sentiment))
    conn.commit()
    cur.close()
    return result

class OpinionStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print("start on status")
        text = status.text.lower()
        if status.truncated:
            text = status.extended_tweet['full_text'].lower()
        if text.endswith('…'):
            return
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
        print('uploading [{}] to postgres'.format(text))
        insert(entity, reason, attitude, sentiment, json.dumps(status._json))

# class FakeStatus():
#     def __init__(self, text):
#         self.text = text
#         self.truncated = False

# fake_status = FakeStatus('i love vague lyrics because the emotions or meaning derived from them is very individualized')
# listener.on_status(fake_status)

# attitude = 'love'
# entity = 'her'
# reason = 'she’s always got cracking stories and doesn’t mind laughing at her self'
# sentiment = 'positive'
# status = '{"created_at": "Tue Jan 28 21:38:52 +0000 2020", "id": 1222272857805185024, "id_str": "1222272857805185024", "text": "@TheChapmanator I love her because she\\u2019s always got cracking stories and doesn\\u2019t mind laughing at her self!", "display_text_range": [16, 107], "source": "<a href=\\"http://tapbots.com/tweetbot\\" rel=\\"nofollow\\">Tweetbot for i\\u039fS</a>", "truncated": false, "in_reply_to_status_id": 1222259716690194432, "in_reply_to_status_id_str": "1222259716690194432", "in_reply_to_user_id": 403582529, "in_reply_to_user_id_str": "403582529", "in_reply_to_screen_name": "TheChapmanator", "user": {"id": 269437320, "id_str": "269437320", "name": "Joseph", "screen_name": "SirJS", "location": "Sydney", "url": null, "description": "\\u201cYou\'ve got a lovely crust\\u201d, said Mary Berry to me. True story.\\n\\n\\ud83c\\uddec\\ud83c\\udde7 expat in \\ud83c\\udde6\\ud83c\\uddfa", "translator_type": "none", "protected": false, "verified": false, "followers_count": 439, "friends_count": 303, "listed_count": 41, "favourites_count": 6206, "statuses_count": 63983, "created_at": "Sun Mar 20 19:44:02 +0000 2011", "utc_offset": null, "time_zone": null, "geo_enabled": true, "lang": null, "contributors_enabled": false, "is_translator": false, "profile_background_color": "DBE9ED", "profile_background_image_url": "http://abs.twimg.com/images/themes/theme17/bg.gif", "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme17/bg.gif", "profile_background_tile": false, "profile_link_color": "CC3366", "profile_sidebar_border_color": "FFFFFF", "profile_sidebar_fill_color": "E6F6F9", "profile_text_color": "333333", "profile_use_background_image": true, "profile_image_url": "http://pbs.twimg.com/profile_images/1212106293734862848/PctliY5W_normal.jpg", "profile_image_url_https": "https://pbs.twimg.com/profile_images/1212106293734862848/PctliY5W_normal.jpg", "profile_banner_url": "https://pbs.twimg.com/profile_banners/269437320/1557954913", "default_profile": false, "default_profile_image": false, "following": null, "follow_request_sent": null, "notifications": null}, "geo": null, "coordinates": null, "place": {"id": "3b68ce804a159b29", "url": "https://api.twitter.com/1.1/geo/id/3b68ce804a159b29.json", "place_type": "neighborhood", "name": "Haymarket", "full_name": "Haymarket, Sydney", "country_code": "AU", "country": "Australia", "bounding_box": {"type": "Polygon", "coordinates": [[[151.199728, -33.885813], [151.199728, -33.877185], [151.209275, -33.877185], [151.209275, -33.885813]]]}, "attributes": {}}, "contributors": null, "is_quote_status": false, "quote_count": 0, "reply_count": 0, "retweet_count": 0, "favorite_count": 0, "entities": {"hashtags": [], "urls": [], "user_mentions": [{"screen_name": "TheChapmanator", "name": "Gary Chapman", "id": 403582529, "id_str": "403582529", "indices": [0, 15]}], "symbols": []}, "favorited": false, "retweeted": false, "filter_level": "low", "lang": "en", "timestamp_ms": "1580247532689"}'
# insert(entity, reason, attitude, sentiment, status)

while True:
    try:
        conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
        like_stream = tweepy.Stream(auth=api.auth, listener=OpinionStreamListener(), tweet_mode='extended')
        like_stream.filter(track=['i like because', 'i love because', 'i admire because', 'i adore because', 'i don\'t like because', 'i hate because', 'i dislike because'])
    except:
        print('exception occurred. Sleeping for 5 seconds. exception was ', sys.exc_info()[0])
        time.sleep(5)
