import logging
import os
import time

from typing import Dict
import json

from chirpy.core.logging_utils import setup_logger, PROD_LOGGER_SETTINGS

from agents.remote_non_persistent import RemoteNonPersistentAgent
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(dbname="session_store", user=os.environ['POSTGRES_USER'], password=os.environ["POSTGRES_PASSWORD"], host=os.environ["POSTGRES_HOST"])
logger = logging.getLogger('chirpylogger')
root_logger = logging.getLogger()
if not hasattr(root_logger, 'chirpy_handlers'):
    setup_logger(PROD_LOGGER_SETTINGS)

class StateTable:
    def __init__(self):
        self.table_name = 'prod_turns_kvstore'

    def fetch(self, session_id, creation_date_time):
        logger.info(
            f"state_table fetching last state for session {session_id}, creation_date_time {creation_date_time} from table {self.table_name}")
        if session_id is None:
            return None
        try:
            item = None
            start_time = time.time()
            timeout = 2  # second
            while (item is None and time.time() < start_time + timeout):
                with conn.cursor() as curs:
                    curs.execute(f"SELECT state from {self.table_name} where session_id=%(session_id)s AND creation_date_time=%(creation_date_time)s",
                                 {'session_id':session_id, 'creation_date_time': creation_date_time})
                    item = curs.fetchone()[0]
                item = {k: json.dumps(v) for k, v in item.items()}
            if item is None:
                logger.error(
                    f"Timed out when fetching last state\nfor session {session_id}, creation_date_time {creation_date_time} from table {self.table_name}.")
            else:
                return item
        except:
            logger.exception("Exception when fetching last state")
            return None

    def persist(self, state: Dict):
        logger.primary_info('Using StateTable to persist state! Persisting to table {}'.format(self.table_name))
        logger.primary_info('session_id: {}'.format(state['session_id']))
        logger.primary_info('creation_date_time: {}'.format(state['creation_date_time']))
        decoded_state = {k: json.loads(v) for k, v in state.items()}
        try:
            assert 'session_id' in state
            assert 'creation_date_time' in state
            assert 'user_id' in state
            with conn.cursor() as curs:
                curs.execute(
                    f"INSERT INTO {self.table_name} (creation_date_time, session_id, user_id, state) VALUES  "
                    f"(%(creation_date_time)s, %(session_id)s, %(user_id)s, %(state)s)",
                    {'session_id': decoded_state['session_id'], 'creation_date_time': decoded_state['creation_date_time'],
                     'user_id': decoded_state['user_id'], 'state': psycopg2.extras.Json(decoded_state)})

            return True
        except:
            logger.error("Exception when persisting state to table" + self.table_name, exc_info=True)
            return False


class UserTable():
    def __init__(self):
        self.table_name = 'prod_users_kvstore'

    def fetch(self, user_id):
        logger.debug(
            f"user_table fetching last state for user {user_id} from table {self.table_name}")
        if user_id is None:
            return None
        try:
            item = None
            start_time = time.time()
            timeout = 2  # second
            while (item is None and time.time() < start_time + timeout):
                with conn.cursor() as curs:
                    curs.execute(f"SELECT attributes from {self.table_name} where user_id=%(user_id)s",
                                 {'user_id':user_id})
                    row = curs.fetchone()
                    if row:
                        item = row[0]
                        item = {k: json.dumps(v) for k,v in item.items()}
                    else:
                        item = {}
            if item is None:
                logger.error(
                    f"Timed out when fetching user attributes\nfor user_id {user_id} from table {self.table_name}.")
            else:
                return item
        except:
            logger.error("Exception when fetching user attributes from table: " + self.table_name,
                         exc_info=True)
            return None

    def persist(self, user_attributes: Dict) -> None:
        """
        This will take the provided user_preferences object and persist it to Postgres.
        """
        try:
            assert 'user_id' in user_attributes
            decoded_attributes = {k: json.loads(v) for k, v in user_attributes.items()}
            with conn.cursor() as curs:
                return curs.execute(
                    f"INSERT INTO {self.table_name} (user_id, attributes) VALUES  "
                    f"(%(user_id)s, %(attributes)s) ON CONFLICT (user_id) DO UPDATE SET attributes=%(attributes)s",
                    {'user_id': decoded_attributes['user_id'], 'attributes': psycopg2.extras.Json(decoded_attributes)})
        except:
            logger.error("Exception when persisting state to table: " + self.table_name, exc_info=True)
            return False

class RemotePersistentAgent(RemoteNonPersistentAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_table = StateTable()
        self.user_table = UserTable()

    def process_utterance(self, user_utterance):

        handler = self.create_handler()
        current_state = self.get_state_attributes(user_utterance)
        user_attributes = self.get_user_attributes()
        last_state = self.get_last_state()

        turn_result = handler.execute(current_state, user_attributes, last_state)
        response = turn_result.response
        try:
            if user_attributes != turn_result.user_attributes:
                self.user_table.persist(turn_result.user_attributes)
            self.state_table.persist(turn_result.current_state)

        except:
            logger.error("Error persisting state")

        conn.commit()
        return response, current_state
