import psycopg2
import os
from chirpy.core.util import get_es_host

host = 'chirpy-postgres.postgres.database.azure.com'
host_stream = 'chirpy-postgres.postgres.database.azure.com'
port = 5432
database = 'twitter_opinions'
user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
conn = psycopg2.connect(host=host_stream, port=port, database=database, user=user, password=password)

def fetch_sql(sql_statement):
    print(sql_statement)
    cur = conn.cursor()
    cur.execute(sql_statement)
    result = cur.fetchall()
    conn.commit()
    cur.close()
    return result

def execute_sql(sql_statement):
    print(sql_statement)
    cur = conn.cursor()
    cur.execute(sql_statement)
    conn.commit()
    cur.close()
    return
#     
# CREATE_DATABASE = """
# create database 
# """
# execute_sql(CREATE_TABLE)

# CREATE_TABLE = """
# create table opinions (
#     id serial primary key,
#     entity varchar(64),
#     reason varchar(256),
#     attitude varchar(16),
#     sentiment varchar(16),
#     creation_date_time timestamp,
#     status jsonb
# );
# """
# execute_sql(CREATE_TABLE)

# DROP_TABLE = """
# drop table labeled_opinions;
# """
# execute_sql(DROP_TABLE)

CREATE_TABLE = """
create table labeled_opinions (
    id serial primary key,
    entity varchar(64),
    reason varchar(256),
    attitude varchar(16),
    sentiment varchar(16),
    reason_appropriateness numeric,
    tweet_id numeric,
    annotator varchar(16),
    creation_date_time timestamp
);
"""
execute_sql(CREATE_TABLE)

# DROP_TABLE = """
# drop table annotator_opinions;
# """
# execute_sql(DROP_TABLE)


CREATE_TABLE = """
create table annotator_opinions (
    id serial primary key,
    annotator varchar(64),
    entity varchar(64),
    entity_appropriate bool,
    sentiment varchar(16),
    creation_date_time timestamp
);
"""
execute_sql(CREATE_TABLE)

# DROP_TABLE = """
# drop table labeled_phrases;
# """
# execute_sql(DROP_TABLE)

CREATE_TABLE = """
create table labeled_phrases (
    id serial primary key,
    phrase varchar(64),
    category varchar(256),
    wiki_entity_name varchar(64),
    good_for_wiki bool,
    creation_date_time timestamp
);
"""
execute_sql(CREATE_TABLE)