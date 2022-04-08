from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
import psycopg2

host_stream = 'twitter-opinions.cx4nfaa5bt0l.us-east-1.rds.amazonaws.com'
# host_stream = 'localhost'
port = 5432
database = 'twitter_opinions'
user = 'postgres'
password = 'qyhqae-4Sepzy-zecget'

def fetch_sql(sql_statement):
    conn = psycopg2.connect(host=host_stream, port=port, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute(sql_statement)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return result

def execute_sql(sql_statement):
    conn = psycopg2.connect(host=host_stream, port=port, database=database, user=user, password=password)
    cur = conn.cursor()
    cur.execute(sql_statement)
    conn.commit()
    cur.close()
    return

def get_ent_group(entity):
    for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
        if ent_group.matches(entity):
            return ent_group_name
    return None

if __name__ == "__main__":
    results = fetch_sql("select * from labeled_phrases_cat where generic = true")

    id_to_wiki_cat = {row[0] : get_ent_group(get_entity_by_wiki_name(row[3])) if row[3] is not None else None for row in results}

    for phrase_id, wiki_cat in id_to_wiki_cat.items():
        if wiki_cat is not None:
            execute_sql(f"update labeled_phrases_cat set wiki_category = '{wiki_cat}' where id = {phrase_id}")
