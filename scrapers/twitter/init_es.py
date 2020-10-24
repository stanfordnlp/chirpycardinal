import boto3
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from chirpy.core.util import get_es_host

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
)

mappings = {
    "properties": {
        "entity" : {"type": "text"},
        "entity_keyword": {"type": "keyword"},
        "reason": {"type": "text"},
        "attitude": {"type": "keyword"},
        "sentiment": {"type": "keyword"},
        "tweet_id": {"type": "text"},
        "original_text": {"type": "text"},
    }
}

es.indices.create(index='opinion', body={'mappings': mappings})
es.indices.delete(index='opinion')
result = es.search(index='opinion', body={
    'query': {'term': {'sentiment': 'positive'}}
})
result = es.search(index='opinion', body={
    'query': {'term': {'entity_keyword': 'minecraft'}}
})
print([hit['_source']['original_text'] for hit in result['hits']['hits']])