from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.annotators.corenlp import Sentiment
from chirpy.response_generators.wiki2.state import ConditionalState
from typing import Optional
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
from chirpy.response_generators.wiki2.response_templates.response_components import *
#from chirpy.response_generators.opinion2.utils import get_reasons
from chirpy.response_generators.wiki2.wiki_helpers import contains_first_person_word
import random

logger = logging.getLogger('chirpylogger')


class GetOpinionTreelet(Treelet):
    """
    Get opinion after asking the user about their interest in topic
    """
    name = "wiki_get_opinion_treelet"

    def get_intro_paragraph(self, entity: str) -> Optional[str]:
        """This method attempts to get a summary of a section. In the future this could be a real
        summarization module

        :param entity: the current resolved WIKI entity
        :type entity: str
        :return: The summary of the section. Currently LEAD-3
        :rtype: str

        >>> treelet = IntroductoryTreelet(None)
        >>> treelet.get_overview('Taylor Swift')
        'Taylor Alison Swift (born December 13, 1989) is an American singer-songwriter.
        She is known for narrative songs about her personal life, which have received widespread media coverage.'
        """
        logger.debug(f'Getting overview for: {entity}')
        overview = wiki_utils.overview_entity(entity, wiki_utils.get_sentseg_fn(self.rg))
        if not overview:
            logger.info("No overview found")
            return None
        return overview

    def get_opinion(self, sentiment, topic):
        pos_reasons, neg_reasons = get_reasons(topic.lower())
        logger.primary_info(f"Wiki pos reasons identified: {pos_reasons}")
        logger.primary_info(f"Wiki neg reasons identified: {neg_reasons}")

        if sentiment in [Sentiment.NEUTRAL, Sentiment.POSITIVE, Sentiment.STRONG_POSITIVE]:
            reasons = pos_reasons
            liking = "like"
        else:
            reasons = neg_reasons
            liking = "dislike"
        if len(reasons) == 0:
            logger.primary_info("No reasons found to form opinion")
            return None
        first_person_reasons = [r for r in reasons if contains_first_person_word(r)]
        non_first_person_reasons = [r for r in reasons if not contains_first_person_word(r)]
        if len(non_first_person_reasons) > 0:
            return f"I know some people {liking} it because {random.choice(non_first_person_reasons)}."
        else:
            return f"Personally, I feel like {random.choice(first_person_reasons)}."

    def get_acknowledgement(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        prefix = ''
        if ResponseType.POS_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types:
                prefix = random.choice(POS_OPINION_RESPONSES)
        elif ResponseType.NEG_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types: # negative opinion
                prefix = "That's an interesting take,"
            else: # expression of sadness
                return random.choice(COMMISERATION_ACKNOWLEDGEMENTS)
        elif ResponseType.NEUTRAL_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types or ResponseType.PERSONAL_DISCLOSURE in response_types:
                return random.choice(NEUTRAL_OPINION_SHARING_RESPONSES)

        if prefix is not None:
            return prefix
            # return self.get_neural_response(prefix=prefix, allow_questions=False) TODO need prefixed neural gen
        return self.get_neural_acknowledgement()

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()

        sentiment = self.get_sentiment()

        if ResponseType.DONT_KNOW in response_types:
            ack = random.choice(["That's alright.", "Sure, no worries."])
        elif ResponseType.NO in response_types:
            ack = random.choice(["Okay, no worries.", "Sure that's fine."])
        else:
            ack = self.get_acknowledgement()
        opinion = self.get_opinion(sentiment, state.cur_entity.name)

        if opinion:
            return ResponseGeneratorResult(
                text=f"{ack} {opinion.lower()}",
                priority=priority, state=state, needs_prompt=False, cur_entity=state.cur_entity,
                conditional_state=ConditionalState(prev_treelet_str=self.name,
                                                   next_treelet_str='transition')
            )
        else:
            discuss_article_response = self.rg.discuss_article_treelet.get_response() #Yeah, I know about Shark's Etymology...
            discuss_article_response.text = f"{ack} {discuss_article_response.text}"
            return discuss_article_response
