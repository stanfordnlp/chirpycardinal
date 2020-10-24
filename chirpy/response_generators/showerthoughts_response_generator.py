import random
import logging
import chirpy.core.offensive_classifier.offensive_classifier as offensive_classify
import chirpy.response_generators.news.news_response_generator_util as news_rg_utils
from chirpy.core.callables import ResponseGenerator

from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator_datatypes import emptyResult, ResponseGeneratorResult, PromptResult, emptyPrompt, \
    UpdateEntity
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger('chirpylogger')

INFORM_SHOWER_THOUGHTS = ['Here\'s a random thought. {}',
                          'You know what I was thinking? {}',
                          'You know what I realized the other day? {}']


@dataclass
class State:
    thread_ids_used: List[str]


@dataclass
class ConditionalState:
    used_thread_id: str


class ShowerThoughtsResponseGenerator(ResponseGenerator):
    name='SHOWER_THOUGHTS'
    def init_state(self) -> State:
        return State(thread_ids_used=[])

    def get_entity(self, state) -> UpdateEntity:
        return UpdateEntity(False)

    def get_response(self, state: State) -> ResponseGeneratorResult:

        # Get the cur_entity
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        if cur_entity is None:
            return emptyResult(state)

        topic = cur_entity.common_name  # lowercase
        logger.primary_info('Chose this topic for Showerthoughts: {}'.format(topic))
        thread = self.get_showerthoughts_result(state, topic)
        if thread:
            logger.primary_info('Chose this ShowerThought thread: {}'.format(thread))
            return ResponseGeneratorResult(text=random.choice(INFORM_SHOWER_THOUGHTS).format(thread['title']),
                                           priority=ResponsePriority.CAN_START, needs_prompt=True, state=state,
                                           cur_entity=cur_entity,
                                           conditional_state=ConditionalState(used_thread_id=thread['threadId']))

        # If we found nothing, return empty response
        return emptyResult(state)

    def get_prompt(self, state: State) -> PromptResult:
        return emptyPrompt(state)

    def get_showerthoughts_result(self, state: State, topic: str) -> Optional[dict]:
        """Fetches a subreddit according to the news-topic."""
        logger.primary_info("Topic: {}, urls banned: {}".format(topic, state.thread_ids_used))
        query = self.showerthoughts(topic.lower(), banned_thread_urls=state.thread_ids_used)
        query_result = news_rg_utils.es.search(index="reddit", body=query)
        if query_result['hits']['hits']:
            logger.primary_info('Queried Reddit index with topic {}, got {} threads'.format(
                topic, len(query_result['hits']['hits'])))
            reddit_thread = self.select_thread(query_result['hits']['hits'], topic.lower())
            if reddit_thread:
                reddit_thread['title'] = news_rg_utils.add_fullstop(reddit_thread['title'])
                return reddit_thread
        return None

    def select_thread(self, thread_list: List[dict], topic: str) -> Optional[List[dict]]:
        """Selects a thread with maximum karma without offensive phrases in the title."""
        thread_list = list(filter(lambda thread: \
                not offensive_classify.contains_offensive(\
                thread['_source']['title']), thread_list))
        # Filter threads whose title doesn't contain the single-worded topics.
        if topic and len(topic.split()) == 1:
            thread_list = list(filter(lambda thread: topic in [word.lower() \
                for word in thread['_source']['title'].split()], thread_list))
        if not thread_list:
            return None
        thread_list = sorted(thread_list, key = lambda thread: \
            int(thread['_source']['karma']), reverse = True)  
        return thread_list[0]['_source']

    def showerthoughts(self, topic: str, banned_thread_urls: List[str]) -> dict:
        """Builds a query matching news-entity in the headline."""
        # TODO: Sort queries by karma value. 
        query = {
                "query":
                        {"bool":
                            {
                                "filter": [
                                    {"match": {"subreddit": "Showerthoughts"}}
                                ],
                                "must": [
                                    {
                                        "bool": {
                                            "must": [{"match": {"title": word}} for word in topic.split()]
                                        }
                                    },
                                ],
                                "must_not": [
                                    {"ids": {"values": banned_thread_urls}}
                                ],
                            }
                        },
            }
        return query 

    def update_state_if_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        state.thread_ids_used.append(conditional_state.used_thread_id)  # Append the thread_id we used
        return state

    def update_state_if_not_chosen(self, state: State, conditional_state: Optional[ConditionalState]) -> State:
        return state

