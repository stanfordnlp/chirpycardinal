import os
import csv
import psycopg2
from typing import List, Tuple
from chirpy.util import get_es_host
ENTITY_CLUSTERS_LINKED = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'entity_clusters_linked.csv')

host = get_es_host("postgres")
host_stream = get_es_host("chirpy_stream")
port = os.environ.get('POSTGRES_PORT')
database = 'twitter_opinions'
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')

def insert(data : List[Tuple[str, str, str, bool]], host : str):
    conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password) # type: ignore
    cur = conn.cursor()
    cleaned_data = [[elem if elem != '' else None for elem in row] for row in data]
    args_str = b','.join(cur.mogrify("(%s, %s, %s, %s, CURRENT_TIMESTAMP)", row) for row in cleaned_data)
    cur.execute(b'insert into labeled_phrases (phrase, category, wiki_entity_name, good_for_wiki, creation_date_time) values ' + args_str)
    conn.commit()
    cur.close()
    conn.close()
    return 


def get_local_entity_clusters_linked() -> List[Tuple[str, str, str, bool]]:
    with open(ENTITY_CLUSTERS_LINKED, 'r') as f:
        rows = list(csv.reader(f))[1:]
        rows = [tuple(row[:-1]) + (row[-1] == 'True',) for row in rows]
    return rows

rows = get_local_entity_clusters_linked()
insert(rows, host_stream)
