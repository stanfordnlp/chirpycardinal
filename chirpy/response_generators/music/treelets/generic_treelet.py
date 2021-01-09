import random

from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST

from chirpy.core.response_priority import ResponsePriority, PromptType

from chirpy.response_generators.music.utils import logger, WikiEntityInterface

from chirpy.response_generators.music.expression_lists import LIKE_CLAUSES, DISLIKE_CLAUSES, CHAT_CLAUSES, SURPRISE_EXPRESSIONS, DRY_EXPRESSIONS, RARE_WORDS
from chirpy.response_generators.music.expression_lists import POSITIVE_FEELINGS, NEGATIVE_FEELINGS
from chirpy.response_generators.music.expression_lists import PositiveTemplate, NegativeTemplate, DontKnowTemplate
from chirpy.response_generators.music.treelets.abstract_treelet import Treelet, TreeletType


TRIGGER_PHRASES = [
    'music'
]

TRIGGER_ENTITY_GROUPS = []

class LikeMusicTemplate(RegexTemplate):
    slots = {
        'like_clause': LIKE_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(?<!don't ){like_clause}" + OPTIONAL_TEXT_MID + "{trigger_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i am a big fan, i like music a lot', {'like_clause': 'like', 'trigger_word': 'music'}),
        ('i like talking about music', {'like_clause': 'like', 'trigger_word': 'music'})
    ]
    negative_examples = [
        'i hate music',
    ]

class DislikeMusicTemplate(RegexTemplate):
    slots = {
        'dislike_clause': DISLIKE_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(?<!don't ){dislike_clause}" + OPTIONAL_TEXT_MID + "{trigger_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i dislike listening to music a lot', {'dislike_clause': 'dislike', 'trigger_word': 'music'})
    ]
    negative_examples = [
        'i love music',
    ]

class ChatMusicTemplate(RegexTemplate):
    slots = {
        'chat_clause': CHAT_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "(?<!don't ){chat_clause} {trigger_word}" + OPTIONAL_TEXT_POST,
        "{trigger_word}"
    ]
    positive_examples = [
        ('let\'s chat about music', {'chat_clause': 'chat about', 'trigger_word': 'music'})
    ]
    negative_examples = [
        'i love music',
    ]

class QuestionListeningFrequencyTemplate(RegexTemplate):
    slots = {
        'frequency_words': ['often', 'frequently'],
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "how {frequency_words} do you listen to {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "do you {frequency_words} listen to {trigger_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('how often do you listen to music', {'frequency_words': 'often', 'trigger_word': 'music'}),
        ('do you frequently listen to music', {'frequency_words': 'frequently', 'trigger_word': 'music'}),
        ('how frequently do you listen to music', {'frequency_words': 'frequently', 'trigger_word': 'music'})
    ]
    negative_examples = [
        'i do not listen to music often',
    ]

FREQUENT_WORDS = ['often', 'frequently', 'a lot', 'a ton', 'always', 'all the time', 'whenever']

class AnswerListeningFrequencyTemplate(RegexTemplate):
    slots = {
        'frequent_words': FREQUENT_WORDS,
        'sometimes_words': ['sometimes', 'time to time'],
        'rare_words': RARE_WORDS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{frequent_words}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{sometimes_words}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{rare_words} {frequent_words}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{rare_words}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('i listen to music whenever i can too, and luckily i have a lot of free time in the cloud', {'frequent_words': 'whenever'}),
        ('i listen to music all the time i\'ve got nothing better to do', {'frequent_words': 'all the time'}),
        ('i never get bored of listening to music either i have my headphones on all the time', {'frequent_words': 'all the time'})
    ]
    negative_examples = [
        'i listen to music',
    ]

class QuestionListeningConditionsTemplate(RegexTemplate):
    slots = {
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "when" + OPTIONAL_TEXT_MID + "{trigger_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('when do you like listening to music', {'trigger_word': 'music'}),
        ('when do you listen to music', {'trigger_word': 'music'})
    ]
    negative_examples = []

class AnswerListeningConditionsTemplate(RegexTemplate):
    slots = {
        'time': ['when', 'while', 'whenever'],
        'rare_words': RARE_WORDS,
        'frequent_words': FREQUENT_WORDS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{time}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{rare_words}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{frequent_words}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('that\'s wonderful! i like listening to music when i do the laundry, but i don\'t have many clothes to wash', {'time': 'when'}),
        ('that\'s great! i am listening to music whenever regardless of what i do', {'time': 'whenever'})
    ]
    negative_examples = []

class QuestionFeelingsAboutMusicTemplate(RegexTemplate):
    slots = {
        'feelings': ['feelings', 'thoughts', 'feel', 'think'],
        'trigger_word': TRIGGER_PHRASES + ['musician', 'song']
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{feelings}" + OPTIONAL_TEXT_MID + "{trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{trigger_word}" + OPTIONAL_TEXT_MID + "{feelings}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('how does music make you feel', {'feelings': 'feel', 'trigger_word': 'music'}),
        ('how does listening to your favorite song make you feel', {'feelings': 'feel', 'trigger_word': 'song'}),
        ('how does listening to your favorite musician make you feel', {'feelings': 'feel', 'trigger_word': 'musician'})
    ]
    negative_examples = []

class AnswerFeelingsAboutMusicTemplate(RegexTemplate):
    slots = {
        'positive_feeling': POSITIVE_FEELINGS,
        'negative_feeling': NEGATIVE_FEELINGS
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{positive_feeling}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{negative_feeling}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('music makes me feel alive', {'positive_feeling': 'alive'}),
        ('it makes me feel sad', {'negative_feeling': 'sad'})
    ]
    negative_examples = []

GENERIC_TEMPLATES = {
    'LikeMusicTemplate': LikeMusicTemplate(),
    'DislikeMusicTemplate': DislikeMusicTemplate(),
    'ChatMusicTemplate': ChatMusicTemplate()
}

QUESTION_TEMPLATES = {
    'QuestionListeningFrequencyTemplate': QuestionListeningFrequencyTemplate(),
    'QuestionListeningConditionsTemplate': QuestionListeningConditionsTemplate(),
    'QuestionFeelingsAboutMusicTemplate': QuestionFeelingsAboutMusicTemplate()
}

ANSWER_TEMPLATES = {
    'QuestionListeningFrequencyTemplate': AnswerListeningFrequencyTemplate(),
    'QuestionListeningConditionsTemplate': AnswerListeningConditionsTemplate(),
    'QuestionFeelingsAboutMusicTemplate': AnswerFeelingsAboutMusicTemplate()
}

SENTIMENT_TEMPLATES = {
    'PositiveTemplate': PositiveTemplate(),
    'NegativeTemplate': NegativeTemplate(),
    'DontKnowTemplate': DontKnowTemplate()
}

CHATTING_EXPRESSIONS = [
    "I like chatting about it a lot!",
    "I can talk about it nonstop!",
    "I love talking about it!"
]

LIKE_REASONS = [
    "Music makes me feel like I have wings, even though I am pretty sure I don\'t.",
    "I would get super bored if I couldn\'t listen to music whenever I wanted to.",
    "I cannot imagine what life would be like without music.",
    "If not for music, how else would I wake up in the morning and get ready for some cloud work?",
    "I believe music is the essence of life!"
]

ACKNOWLEDGE_DISLIKE = [
    "that being said, people can have different opinions.",
    "on the other hand, i understand that not everyone likes music.",
    "but, people are different, and so are their opinions.",
    "even though i like music, i understand that you may not like it."
]

ANSWER_LISTENING_FREQUENCY_RARE = [
    "Yeah, I don\'t listen to music too often either, I just like to have some noise around from time to time.",
    "I see. Well, I feel like I have to listen to music, otherwise life gets so boring.",
    "Oh okay. I realized that listening to music while doing work at the same time is hard, so I started listening less frequently as well.",
    "Yeah, I used to have my headphones on all the time, but I have been so busy lately, and don\'t have time for that anymore."
]

ANSWER_LISTENING_FREQUENCY_FREQUENT = [
    "I listen to music whenever I can too. Luckily, I have a ton of free time here in the cloud.",
    "I listen to music all the time as well! I've got nothing better to do.",
    "I never get bored of listening to music either! I have my headphones on all the time.",
    "Same here, I don't know if I could go a day without music. I am listening to a song all the time.",
    "I never get tired of listening to music either, it brings joy to my life."
]

ANSWER_LISTENING_CONDITIONS_FREQUENT = [
    "I like listening to music when I do the laundry, but I don\'t have many clothes to wash.",
    "I try to listen to music when I am studying, but I feel like it distracts me a bit.",
    "I especially like listening to music while I am driving, it makes the time fly faster."
]

ANSWER_FEELINGS_POSITIVE = [
    "Music makes me feel alive. When I am listening to a piece of music that I love, it is hard to express my feelings, I\'m so overwhelmed by emotions.",
    "I think music demonstrates the best of humanity, it fills me with so much awe. I don\'t know what I would do without music.",
    "I don\'t know how to describe my feelings, I would definitely feel incomplete without music."
]

TRANSITIONS = [
    "Music is one of my favorite things and I was wondering if we could talk about it. ",
    "I have a question for you about music. ",
    "There's so much music here in the cloud and I'm curious to know what you think about it. ",
    "I've been listening to a lot of new songs lately, and I'd love to hear what you think about music. "
]

# 'QuestionListeningFrequencyTemplate' is quite similar to 'QuestionListeningConditionsTemplate'. We are
# removing one of these randomly in every conversation.
try:
    question = random.choice(['QuestionListeningConditionsTemplate', 'QuestionListeningConditionsTemplate'])
    del QUESTION_TEMPLATES[question]
except KeyError as e:
    logger.error("We caught an error in Music RG. Key {} didn't exist in {}, but we tried to remove it.".format(question, QUESTION_TEMPLATES))


class GenericTreelet(Treelet):

    def __init__(self, rg):
        super().__init__(rg)
        self.name = "generic"
        self.repr = "Generic Treelet"
        self.treelet_type = TreeletType.HEAD
        self.templates = {**QUESTION_TEMPLATES, **QUESTION_TEMPLATES}
        self.trigger_phrases = self.get_trigger_phrases()
        self.trigger_entity_groups = self.get_trigger_entity_groups()

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

        if state.last_turn_asked_question == 'QuestionListeningFrequencyTemplate':
            response = self._handle_answer_listening_frequency_question(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionListeningConditionsTemplate':
            response = self._handle_answer_listening_conditions_question(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionFeelingsAboutMusicTemplate':
            response = self._handle_answer_feelings_about_music_question(state, triggered_answers)
        else:
            # Last turn was a question, but we don't have a matching template. This should not have happened.
            error_message = "Last turn question {} is not a part of {}. This is not supposed to happen.".format(state.last_turn_asked_question, self.name)
            logger.error(error_message)
            response = self.get_handoff_response(self.state_manager, state)
        return response

    def get_response_trigger_phrase(self, state, trigger_phrase):
        utterance = self.state_manager.current_state.text
        triggered_templates = self.process_templates(self.templates, utterance)

        if 'LikeMusicTemplate' in triggered_templates:
            response = self._handle_expression_like_music(state, triggered_templates)
        elif 'DislikeMusicTemplate' in triggered_templates:
            response = self._handle_expression_dislike_music(state, triggered_templates)
        elif 'ChatMusicTemplate' in triggered_templates:
            response = self._handle_expression_chat_music(state, triggered_templates)
        elif 'QuestionListeningFrequencyTemplate' in triggered_templates:
            response = self._handle_question_listening_frequency(state, triggered_templates)
        elif 'QuestionListeningConditionsTemplate' in triggered_templates:
            response = self._handle_question_listening_conditions(state, triggered_templates)
        elif 'QuestionFeelingsAboutMusicTemplate' in triggered_templates:
            response = self._handle_question_feelings_about_music(state, triggered_templates)
        else:
            # We do not have a matching template. We are responding with generic chat music template answers.
            response = self._handle_expression_chat_music(state, triggered_templates)

        return response

    def get_prompt(self, state, conditional_state=None, trigger_entity = None):
        # Generic treelet only has generic prompts.
        question_candidates = [q for q in list(QUESTION_TEMPLATES.keys()) if q not in state.asked_questions]

        if question_candidates:
            question_name = self.choose(question_candidates)
            question = self.construct_response_from_templates(QUESTION_TEMPLATES, question_name, question=True)
            transition = random.choice(TRANSITIONS)
            prompt = self.prepare_prompt_result(" ".join((transition, question)), state,
                                                priority=PromptType.GENERIC,
                                                cur_entity=WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC),
                                                conditional_state=conditional_state)
            prompt.conditional_state.turn_treelet_history.append(self.name)
            prompt.conditional_state.asked_question = question_name
            prompt.conditional_state.next_treelet = self.name
            prompt.conditional_state.needs_internal_prompt = False
            return prompt
        return None

    def _handle_answer_listening_frequency_question(self, state, triggered_answers):
        question_name = 'QuestionListeningFrequencyTemplate'

        # Determine which response we should give.
        is_rare_response = False
        if question_name in triggered_answers:
            if 'rare_words' in triggered_answers[question_name] or 'sometimes_words' in triggered_answers[question_name]:
                is_rare_response = True
        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            is_rare_response = True

        # Construct the response
        if is_rare_response:
            response = self.choose(ANSWER_LISTENING_FREQUENCY_RARE)
        else:
            surprise_expression = random.choice(SURPRISE_EXPRESSIONS)
            frequent_response = self.choose(ANSWER_LISTENING_FREQUENCY_FREQUENT)
            response = "{} {}".format(surprise_expression, frequent_response)

        # Prepare and return the RG result
        rg_result = self.prepare_rg_result(response, state)

        # Set the needs_prompt to True if we are not engaging the user
        if is_rare_response:
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)

        return rg_result

    def _handle_answer_listening_conditions_question(self, state, triggered_answers):
        question_name = 'QuestionListeningConditionsTemplate'

        # Determine which response we should give.
        is_rare_response = False
        if question_name in triggered_answers and 'rare_words' in triggered_answers[question_name]:
            is_rare_response = True
        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            is_rare_response = True

        # Construct the response
        if is_rare_response:
            response = self.choose(ANSWER_LISTENING_FREQUENCY_RARE)
        else:
            surprise_expression = random.choice(SURPRISE_EXPRESSIONS)
            frequent_response = self.choose(ANSWER_LISTENING_CONDITIONS_FREQUENT)
            response = "{} {}".format(surprise_expression, frequent_response)

        # Prepare and return the RG result
        rg_result = self.prepare_rg_result(response, state)

        # Set the needs_prompt to True if we are not engaging the user
        if is_rare_response:
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)

        return rg_result

    def _handle_answer_feelings_about_music_question(self, state, triggered_answers):
        question_name = 'QuestionFeelingsAboutMusicTemplate'

        # Determine which response we should give.
        is_negative_response = False
        if question_name in triggered_answers and 'negative_feeling' in triggered_answers[question_name]:
            is_negative_response = True
        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            is_negative_response = True

        # Construct the response
        if is_negative_response:
            dry_expression = self.choose(DRY_EXPRESSIONS)
            positive_response = self.choose(ANSWER_FEELINGS_POSITIVE)
            response = "{} {}".format(dry_expression, positive_response)
        else:
            surprise_expression = random.choice(SURPRISE_EXPRESSIONS)
            positive_response = self.choose(ANSWER_FEELINGS_POSITIVE)
            response = "{} {}".format(surprise_expression, positive_response)

        # Prepare and return the RG result
        rg_result = self.prepare_rg_result(response, state)

        # Set the needs_prompt to True if we are not engaging the user
        if is_negative_response:
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)

        return rg_result

    def _handle_expression_like_music(self, state, triggered_templates):
        expression_name = 'LikeMusicTemplate'
        like_reason = self.choose(LIKE_REASONS)
        surprise_expression = random.choice(SURPRISE_EXPRESSIONS)
        response = "{} {}".format(surprise_expression, like_reason)
        rg_result = self.prepare_rg_result(response, state)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)
        return rg_result

    def _handle_expression_dislike_music(self, state, triggered_templates):
        expression_name = 'DislikeMusicTemplate'
        like_reason = self.choose(LIKE_REASONS)
        dry_expression = self.choose(DRY_EXPRESSIONS)
        acknowledge_dislike = self.choose(ACKNOWLEDGE_DISLIKE)
        response = "{} {} {}".format(dry_expression, like_reason, acknowledge_dislike)
        rg_result = self.prepare_rg_result(response, state, needs_prompt=True)
        rg_result.conditional_state.needs_internal_prompt = False
        return rg_result

    def _handle_expression_chat_music(self, state, triggered_templates):
        expression_name = 'ChatMusicTemplate'
        like_reason = self.choose(LIKE_REASONS)
        chatting_expression = "" # self.choose(CHATTING_EXPRESSIONS)
        response = "{} {}".format(like_reason, chatting_expression)
        rg_result = self.prepare_rg_result(response, state)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)
        return rg_result

    def _handle_question_listening_frequency(self, state, triggered_templates):
        question_name = 'QuestionListeningFrequencyTemplate'
        # Construct our answer from the example answers
        response = self.choose(ANSWER_LISTENING_FREQUENCY_FREQUENT)
        rg_result = self.prepare_rg_result(response, state)
        rg_result = self._update_remaining_prompts(rg_result, question_name)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)
        return rg_result

    def _handle_question_listening_conditions(self, state, triggered_templates):
        question_name = 'QuestionListeningConditionsTemplate'
        # Construct our answer from the example answers
        response = self.choose(ANSWER_LISTENING_CONDITIONS_FREQUENT)
        rg_result = self.prepare_rg_result(response, state)
        rg_result = self._update_remaining_prompts(rg_result, question_name)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)
        return rg_result

    def _handle_question_feelings_about_music(self, state, triggered_templates):
        question_name = 'QuestionFeelingsAboutMusicTemplate'
        response = self.choose(ANSWER_FEELINGS_POSITIVE)
        rg_result = self.prepare_rg_result(response, state)
        rg_result = self._update_remaining_prompts(rg_result, question_name)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSIC)
        return rg_result

    def _update_remaining_prompts(self, rg_result, question_name):
        question_candidates = [q for q in list(QUESTION_TEMPLATES.keys()) if q not in rg_result.state.asked_questions]
        if len(question_candidates) == 1:
            rg_result.conditional_state.cannot_prompt.append(self.name) # We ran out of prompts
        rg_result.conditional_state.used_question = question_name
        return rg_result
