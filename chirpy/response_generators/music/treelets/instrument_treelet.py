import random

from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_generator_datatypes import emptyResult, emptyPrompt

from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST

from chirpy.response_generators.music.utils import logger, WikiEntityInterface
from chirpy.response_generators.music.expression_lists import SURPRISE_EXPRESSIONS, TO_BE, CHAT_CLAUSES, LIKE_CLAUSES, POSITIVE_ADJECTIVES, POSITIVE_ADVERBS, ANSWER_FAVORITE_TEMPLATES, MANY_RESPONSES
from chirpy.response_generators.music.expression_lists import PositiveTemplate, NegativeTemplate, DontKnowTemplate
from chirpy.response_generators.music.treelets.abstract_treelet import Treelet, TreeletType


TRIGGER_PHRASES = [
    'instrument',
    'instruments',
    'musical instrument',
    'musical instruments'
]


TRIGGER_ENTITY_GROUPS = []


class ChatInstrumentTemplate(RegexTemplate):
    slots = {
        'chat_clause': CHAT_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(?<!don't ){chat_clause} {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "(?<!don't ){chat_clause} {trigger_word}s" + OPTIONAL_TEXT_POST,
        "{trigger_word}"
    ]
    positive_examples = [
        ('let\'s chat about instruments', {'chat_clause': 'chat about', 'trigger_word': 'instruments'})
    ]
    negative_examples = [
        'i love instruments',
    ]

class QuestionFavoriteInstrumentTemplate(RegexTemplate):
    slots = {
        'like_word': LIKE_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "what is your favorite {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what are your favorite {trigger_word}s" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "do you have a favorite {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what {trigger_word} do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what {trigger_word}s do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what is a {trigger_word} you would like to play" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "if you were a {trigger_word} which one would you be" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ('what is your favorite instrument', {'trigger_word': 'instrument'}),
        ('if you were a musical instrument which one would you be', {'trigger_word': 'musical instrument'}),
        ('what is a musical instrument you would like to play', {'trigger_word': 'musical instrument'}),

    ]
    negative_examples = []

class AnswerFavoriteInstrumentTemplate(RegexTemplate):
    slots = {
        'like_word': LIKE_CLAUSES,
        'answer': NONEMPTY_TEXT,
        'trigger_word': TRIGGER_PHRASES,
        'positive_adverb': POSITIVE_ADVERBS,
        'positive_adjective': POSITIVE_ADJECTIVES,
    }
    templates = ANSWER_FAVORITE_TEMPLATES
    positive_examples = [
        ('my favorite instrument is piano', {'trigger_word': 'instrument', 'answer': 'piano'}),
        ('my favorite instrument is guitar', {'trigger_word': 'instrument', 'answer': 'guitar'})
    ]
    negative_examples = []

GENERIC_TEMPLATES = {
    'ChatInstrumentTemplate': ChatInstrumentTemplate()
}

QUESTION_TEMPLATES = {
    'QuestionFavoriteInstrumentTemplate': QuestionFavoriteInstrumentTemplate()
}

ANSWER_TEMPLATES = {
    'QuestionFavoriteInstrumentTemplate': AnswerFavoriteInstrumentTemplate()
}

SENTIMENT_TEMPLATES = {
    'PositiveTemplate': PositiveTemplate(),
    'NegativeTemplate': NegativeTemplate(),
    'DontKnowTemplate': DontKnowTemplate()
}

CHAT_INSTRUMENT_EXPRESSIONS = [
    "I enjoy talking about instruments, or anything related to music really!",
    "I am a big fan of music instruments, they make it possible for humans to express themselves in myriad different ways.",
    "I always enjoy chatting about music, I love that there are a ton of musical instruments out there, ready for the next Mozart to come and make great things."
]

ACKNOWLEDGE_FAVORITE_INSTRUMENT = [
    "I tried learning how to play the ENTITY when I was a kid, but I was never good at it. I enjoy listening to someone else play it though.",
    "I always wanted to learn how to play ENTITY, but I never found the time to focus and practice.",
    "Listening to ENTITY always takes me to wonderful places.",
    "That is definitely a good one! For me, I have trouble picking which instrument I like the most, but ENTITY is definitely high up on my list.",
    "Who doesn\'t like ENTITY! I am always amazed at the quality of the performances I keep seeing online.",
    "I had a friend who was an amazing ENTITY player. I used to watch her perform live, but that was a while ago."
]

ACKNOWLEDGE_FAVORITE_INSTRUMENT_NEGATIVE = [
    "Not everybody has a favorite instrument, I am not sure if I have one either.",
    "Same here, not sure if I have a favorite instrument either.",
    "Yeah, I guess I don\'t have a favorite instrument either."
]

ACKNOWLEDGE_FAVORITE_INSTRUMENT_NEVER_HEARD = [
    "Ah, sorry I didn\'t catch the name of the instrument you mentioned. Looks like I need to do more reading and googling.",
    "Hmm, I couldn\'t recognize the instrument you mentioned. I guess I need to expand my knowledge of different instruments!",
    "Oh, I\'m having trouble catching the name of the instrument you mentioned. I am guessing that I need to go back to high school and listen to my music professor carefully this time.",
]

FAVORITE_INSTRUMENT_FOLLOWUP_QUESTIONS = [
    "Why do you like ENTITY so much?",
    "What made you like ENTITY so much?",
    "I would be interested in why you like ENTITY. What makes you like it?"
]

ACKNOWLEDGE_FAVORITE_INSTRUMENT_FOLLOWUP_NEGATIVE = [
    "Oh, got it!",
    "Okay!",
    "Sounds good!",
    "I see."
]

ACKNOWLEDGE_FAVORITE_INSTRUMENT_FOLLOWUP_POSITIVE = [
    "That\'s super interesting, thank you for sharing!",
    "Wow, I wish I had strong feelings for an instrument too.",
    "That is great to know, thank you so much for sharing!"
]

TRANSITIONS = [
    "I've been trying to find some new hobbies and I've been thinking about learning to play a musical instrument. ",
    "I've been listening to some new music today and I wanted to chat about instruments. ",
    "I'm really passionate about music and I'm curious what you think about instruments. "
]

class InstrumentTreelet(Treelet):

    def __init__(self, rg):
        super().__init__(rg)
        self.name = "instrument"
        self.repr = "Instrument Treelet"
        self.treelet_type = TreeletType.HEAD
        self.trigger_phrases = self.get_trigger_phrases()
        self.trigger_entity_groups = self.get_trigger_entity_groups()
        self.templates = {**QUESTION_TEMPLATES}

    @staticmethod
    def get_trigger_phrases():
        return TRIGGER_PHRASES

    @staticmethod
    def get_trigger_entity_groups():
        return TRIGGER_ENTITY_GROUPS

    def get_response_last_turn_asked_question(self, state):
        utterance = self.state_manager.current_state.text
        triggered_answers = self.process_templates(ANSWER_TEMPLATES, utterance)
        sentiment_answers = self.process_templates(SENTIMENT_TEMPLATES, utterance)
        triggered_answers = {**triggered_answers, **sentiment_answers}

        if state.last_turn_asked_question == 'QuestionFavoriteInstrumentTemplate':
            response = self._handle_answer_favorite_question(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionFavoriteInstrumentTemplate Followup 1':
            response = self._handle_answer_favorite_question_followup1(state, triggered_answers)
        else:
            # Last turn was a question, but we don't have a matching template. This should not have happened.
            error_message = "Last turn question {} is not a part of {}. This is not supposed to happen.".format(state.last_turn_asked_question, self.name)
            logger.error(error_message)
            response = self.get_handoff_response(self.state_manager, state)
        return response

    def get_response_trigger_phrase(self, state, trigger_phrase = None):
        utterance = self.state_manager.current_state.text
        triggered_templates = self.process_templates(self.templates, utterance)

        if 'QuestionFavoriteInstrumentTemplate' in triggered_templates:
            response = self._handle_question_favorite(state, triggered_templates)
        else:
            response = self._handle_expression_chat_instrument(state, triggered_templates)

        return response

    def get_prompt(self, state, conditional_state=None, trigger_entity = None):
        # Instrument treelet only has generic prompts.
        question_candidates = [q for q in list(QUESTION_TEMPLATES.keys()) if q not in state.asked_questions]
        if question_candidates:
            question_name = self.choose(question_candidates)
            question = self.construct_response_from_templates(QUESTION_TEMPLATES, question_name, question=True)
            transition = random.choice(TRANSITIONS)
            prompt = self.prepare_prompt_result(" ".join((transition, question)), state,
                                                priority=PromptType.GENERIC,
                                                cur_entity=WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.INSTRUMENT),
                                                conditional_state=conditional_state)
            prompt.conditional_state.turn_treelet_history.append(self.name)
            prompt.conditional_state.asked_question = question_name
            prompt.conditional_state.next_treelet = self.name
            prompt.conditional_state.needs_internal_prompt = False
            prompt.expected_type = WikiEntityInterface.EntityGroup.INSTRUMENT
            return prompt
        return None

    def _handle_answer_favorite_question(self, state, triggered_answers):
        question_name = 'QuestionFavoriteInstrumentTemplate'

        # Check if the user mentioned an instrument.
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        instrument_entity = None
        if cur_entity and WikiEntityInterface.is_in_entity_group(cur_entity, WikiEntityInterface.EntityGroup.INSTRUMENT):
            instrument_entity = cur_entity
        elif question_name in triggered_answers and 'answer' in triggered_answers[question_name]:
            instrument_name = triggered_answers[question_name]['answer']
            instrument_entity = WikiEntityInterface.link_span(instrument_name.capitalize())

        # If the user mentioned an instrument, ask a follow up question.
        if instrument_entity:
            response = self.choose(ACKNOWLEDGE_FAVORITE_INSTRUMENT)
            followup = self.choose(FAVORITE_INSTRUMENT_FOLLOWUP_QUESTIONS)
            response = "{} {}".format(response, followup)
            response = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, instrument_entity.common_name)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.cur_entity = instrument_entity
            rg_result.conditional_state.asked_question = 'QuestionFavoriteInstrumentTemplate Followup 1'
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.conditional_state.next_treelet = self.name
        # If not, acknowledge the user response and exit the Music RG.
        elif self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_FAVORITE_INSTRUMENT_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            response  = self.choose(ACKNOWLEDGE_FAVORITE_INSTRUMENT_NEVER_HEARD)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True

        return rg_result

    def _handle_answer_favorite_question_followup1(self, state, triggered_answers):
        question_name = 'QuestionFavoriteInstrumentTemplate Followup 1'

        # If the user gives a negative or don't know answer, end to conversation.
        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_FAVORITE_INSTRUMENT_FOLLOWUP_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
            if 'DontKnowTemplate' in triggered_answers:
                rg_result.cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        else:
            response = self.choose(ACKNOWLEDGE_FAVORITE_INSTRUMENT_FOLLOWUP_POSITIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
            rg_result.cur_entity = self.state_manager.current_state.entity_tracker.cur_entity

        return rg_result

    def _handle_question_favorite(self, state, triggered_templates):
        # Construct our answer from the example answers
        response = self.choose(MANY_RESPONSES)
        rg_result = self.prepare_rg_result(response, state)
        return rg_result

    def _handle_expression_chat_instrument(self, state, triggered_templates):
        expression_name = 'ChatInstrument'
        response = self.choose(CHAT_INSTRUMENT_EXPRESSIONS)
        rg_result = self.prepare_rg_result(response, state)
        #rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.INSTRUMENT)
        return rg_result
