import random

from chirpy.core.response_priority import ResponsePriority, PromptType

from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST

from chirpy.response_generators.music.utils import KnowledgeInterface, WikiEntityInterface, MusicEntity, logger, Pronoun, REPEAT_THRESHOLD
from chirpy.response_generators.music.expression_lists import TO_BE, LIKE_CLAUSES, POSITIVE_ADJECTIVES, POSITIVE_ADVERBS
from chirpy.response_generators.music.expression_lists import ANSWER_FAVORITE_TEMPLATES, SURPRISE_EXPRESSIONS, MANY_RESPONSES
from chirpy.response_generators.music.expression_lists import PositiveTemplate, NegativeTemplate, DontKnowTemplate
from chirpy.response_generators.music.treelets.abstract_treelet import Treelet, TreeletType


TRIGGER_PHRASES = [
    'musician',
    'musicians',
    'singer',
    'singers',
    'band',
    'bands'
]


TRIGGER_ENTITY_GROUPS = [
    WikiEntityInterface.EntityGroup.MUSICIAN
]

EXAMPLE_MUSICIAN_WIKI_PAGES = {
    #"Drake (musician)": Pronoun.Sex.MALE,
    #"Dua Lipa": Pronoun.Sex.FEMALE,
    #"Harry Styles": Pronoun.Sex.MALE
}

class QuestionLikedMusicianTemplate(RegexTemplate):
    slots = {
        'like_word': LIKE_CLAUSES,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "who are some of the {trigger_word}(s|) you like" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "who are your favorite {trigger_word}s" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "which {trigger_word} do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "which {trigger_word}s do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what is your favorite {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what are your favorite {trigger_word}s" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what {trigger_word} do you {like_word} the most" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what {trigger_word}s do you {like_word} the most" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "do you have a favorite {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "who is your favorite {trigger_word}" + OPTIONAL_TEXT_POST
    ]
    positive_examples = [
        ('which musicians do you like', {'trigger_word': 'musicians', 'like_word': 'like'}),
        ('which bands do you like', {'trigger_word': 'bands', 'like_word': 'like'})
    ]
    negative_examples = []

class AnswerLikedMusicianTemplate(RegexTemplate):
    slots = {
        'like_word': LIKE_CLAUSES,
        'answer': NONEMPTY_TEXT,
        'trigger_word': TRIGGER_PHRASES,
        'positive_adverb': POSITIVE_ADVERBS,
        'positive_adjective': POSITIVE_ADJECTIVES,
    }
    templates = ANSWER_FAVORITE_TEMPLATES
    positive_examples = [
        ('my favorite musician is ENTITY', {'trigger_word': 'musician', 'answer': 'ENTITY'}),
        ('my favorite singer is ENTITY', {'trigger_word': 'singer', 'answer': 'ENTITY'}),
        ('my favorite band is ENTITY', {'trigger_word': 'band', 'answer': 'ENTITY'})
    ]
    negative_examples = []

QUESTION_TEMPLATES = {
    'QuestionLikedMusicianTemplate': QuestionLikedMusicianTemplate()
}

ANSWER_TEMPLATES = {
    'QuestionLikedMusicianTemplate': AnswerLikedMusicianTemplate()
}

SENTIMENT_TEMPLATES = {
    'PositiveTemplate': PositiveTemplate(),
    'NegativeTemplate': NegativeTemplate(),
    'DontKnowTemplate': DontKnowTemplate()
}


QUESTION_DO_YOU_LIKE = [
    "Do you listen to ENTITY often?",
    "Do you enjoy listening to ENTITY?",
    "Are you a fan of ENTITY?",
    "Is ENTITY one of your favorites?"
]

QUESTION_DO_YOU_LIKE_POPULAR = [
    "It seems like everyone is listening to ENTITY nowadays, what do you think about {} music?".format(Pronoun.Placeholder.POSSESSIVE),
    "ENTITY has been pretty popular lately. Are you a fan of {} songs too?".format(Pronoun.Placeholder.POSSESSIVE),
    "ENTITY has quite a few popular songs nowadays. Do you listen to {}?".format(Pronoun.Placeholder.OBJECT)
]

ACKNOWLEDGE_MENTIONED_MUSICIAN = [
    "Listening to ENTITY makes my whole day better.",
    "ENTITY takes my breath away!",
    "ENTITY really connects with me, I love listening to their songs!",
    "Oh yeah, I wish I could see ENTITY in concert! One day, maybe.",
]

ACKNOWLEDGE_LIKED_MUSICIAN_NEGATIVE = [
    "Okay!",
    "I see.",
    "Alrighty!",
    "Alright!",
    "Okie dokie."
]

ACKNOWLEDGE_LIKED_MUSICIAN = [
    "Me too!",
    "Same here!",
    "Wow!",
    "That\'s great to hear!"
]


# Which of their other songs you know (THIS SHOULD NOT ASK LIKE)
QUESTION_OTHER_SONGS = [
    "What are some other songs you like from ENTITY?",
    "What are some other songs by ENTITY that you like?",
    "What other songs you like by ENTITY?"
]

ACKNOWLEDGE_LIKED_SONGS = [
    "Wow, that sounds great!",
    "I now know what I should listen next when I put my headphones back on.",
    "Oh, wonderful!",
    "You definitely have a good taste in music. Thank you for sharing!"
]

ACKNOWLEDGE_LIKED_SONGS_NEGATIVE = [
    "Okay!",
    "I see.",
    "Alrighty!",
    "Alright!",
    "Okie dokie."
]

EXPRESS_INTEREST_OTHER_SONG = [
    "I love SONG_ENTITY, I listen to it on repeat.",
    "I recently discovered SONG_ENTITY, and I loved it.",
    "Wasn\'t SONG_ENTITY MUSICIAN_ENTITY's song? I used to listen to it a lot.",
    "I heard a lot of my friends mention SONG_ENTITY, but I didn\'t check it out myself yet."
]

NO_ENTITY_TRANSITIONS = [
    "I'm always listening to music and I love discovering new artists. ",
    "A fun fact about me is that I listen to new music every day. I'm curious about which artists you listen to. ",
    "I'm wondering what kind of music you listen to. "
]

ENTITY_TRANSITIONS = [
    "I was wondering if we could talk about musicians. ",
    "I wanted to chat about musicians. ",
    "People have been talking to me about music, and "
]

QUESTION_COULD_YOU_REPEAT = [
    "Hmm, I couldn\'t get the name you mentioned. Would you mind repeating it?",
    "I\'m having trouble understanding the name you mentioned. Could you repeat it?",
    "Ah, sorry, what is it again?",
    "Oops! I couldn't hear you well. What was the name of you mentioned?"
]

ACKNOWLEDGE_COULDNT_GET_MUSICIAN = [
    "Ah, I couldn't recognize the musician. Let\'s see what else we can chat about.",
    "I am having trouble catching the musicians name. Let\'s chat about something else.",
    "Looks like I couldn\'t recognize the musician name. Maybe we should talk about something else."
]

CHAT_MUSICIAN_EXPRESSIONS = [
    "I enjoy talking about musicians! Anything related to music really!",
    "I love chatting about musicians! I love anything related to music!",
    "I love chatting about anything related to music!"
]

class MusicianTreelet(Treelet):

    def __init__(self, rg):
        super().__init__(rg)
        self.name = "musician"
        self.repr = "Musician Treelet"
        self.can_prompt = True
        self.treelet_type = TreeletType.HEAD
        self.trigger_phrases = self.get_trigger_phrases()
        self.trigger_entity_groups = self.get_trigger_entity_groups()
        self.templates = {**QUESTION_TEMPLATES}
        self.favorite = None

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

        if state.last_turn_asked_question == 'QuestionLikedMusicianTemplate':
            response = self._handle_answer_like_question(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionWhichOfTheirSongsDoYouLike':
            response = self._handle_answer_liked_songs(state, triggered_answers)
        else:
            # Last turn was a question, but we don't have a matching template. This should not have happened.
            error_message = "Last turn question {} is not a part of {}. This is not supposed to happen.".format(state.last_turn_asked_question, self.name)
            logger.error(error_message)
            response = self.get_handoff_response(self.state_manager, state)
        return response

    def get_response_trigger_entity(self, state, trigger_entity = None):
        acknowledgment = random.choice([self.choose(ACKNOWLEDGE_MENTIONED_MUSICIAN), ''])
        question = self.choose(QUESTION_DO_YOU_LIKE)
        response = "{} {}".format(acknowledgment, question)
        response = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, trigger_entity.common_name)
        rg_result = self.prepare_rg_result(response, state, cur_entity=trigger_entity)
        rg_result.conditional_state.song_entity = MusicEntity(pref_label=trigger_entity.common_name,
                                                           wiki_entity=trigger_entity)
        rg_result.conditional_state.discussed_entities.append(trigger_entity)
        rg_result.conditional_state.asked_question = 'QuestionLikedMusicianTemplate'  # This is the handler function for the question we are asking.
        rg_result.conditional_state.next_treelet = self.name
        rg_result.conditional_state.needs_internal_prompt = False
        rg_result.conditional_state.musician_entity = MusicEntity(pref_label=trigger_entity, wiki_entity=trigger_entity)
        rg_result.conditional_state.acknowledged_entity = True
        return rg_result

    def get_response_trigger_phrase(self, state, trigger_phrase = None):
        utterance = self.state_manager.current_state.text
        triggered_templates = self.process_templates(QUESTION_TEMPLATES, utterance)
        sentiment_answers = self.process_templates(SENTIMENT_TEMPLATES, utterance)
        triggered_templates = {**triggered_templates, **sentiment_answers}
        undiscussed_titles = [title for title in EXAMPLE_MUSICIAN_WIKI_PAGES.keys() if
                              not WikiEntityInterface.is_title_in_entities(title, state.discussed_entities)]
        trigger_entity = None
        if trigger_phrase:
            trigger_entity = WikiEntityInterface.link_span(trigger_phrase)
            if trigger_entity and not WikiEntityInterface.is_in_entity_group(trigger_entity, WikiEntityInterface.EntityGroup.MUSICIAN):
                trigger_entity = None

        if 'QuestionLikedMusicianTemplate' in triggered_templates:
            response = self._handle_question_like(state, triggered_templates)
        elif trigger_entity:
            response = self.get_response_trigger_entity(state, trigger_entity)
        elif undiscussed_titles:
            selected_title = undiscussed_titles[0]
            cur_entity = WikiEntityInterface.get_by_name(selected_title)
            question = self.choose(QUESTION_DO_YOU_LIKE_POPULAR)
            question = Pronoun.replace_pronouns(question, EXAMPLE_MUSICIAN_WIKI_PAGES[selected_title])
            question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, cur_entity.common_name)
            response = self.prepare_rg_result(question, state, cur_entity=cur_entity)
            response.conditional_state.musician_entity = MusicEntity(pref_label=cur_entity.common_name, wiki_entity=cur_entity)
            response.conditional_state.discussed_entities.append(cur_entity)
            response.conditional_state.asked_question = 'QuestionLikedMusicianTemplate' # This is the handler function for the question we are asking.
            response.conditional_state.next_treelet = self.name
            response.conditional_state.needs_internal_prompt = False
        else:
            response = self._handle_expression_chat_musician(state, None)
        return response

    def get_prompt(self, state, conditional_state=None, trigger_entity = None):
        question_candidates = [q for q in list(QUESTION_TEMPLATES.keys()) if q not in state.asked_questions]
        is_correct_entity_group = trigger_entity and WikiEntityInterface.is_in_entity_group(trigger_entity, WikiEntityInterface.EntityGroup.MUSICIAN)
        undiscussed_titles = [title for title in EXAMPLE_MUSICIAN_WIKI_PAGES.keys() if
                              not WikiEntityInterface.is_title_in_entities(title, state.discussed_entities)]

        # Prepare prompt.
        prompt = self.prepare_prompt_result('Placeholder', state,
                                            priority=PromptType.GENERIC,
                                            cur_entity=None,
                                            conditional_state=conditional_state)
        prompt.conditional_state.turn_treelet_history.append(self.name)
        prompt.conditional_state.next_treelet = self.name
        prompt.conditional_state.needs_internal_prompt = False

        # Give current topic response if possible.
        if trigger_entity and is_correct_entity_group:
            prompt.priority = PromptType.CURRENT_TOPIC
            prompt.cur_entity = trigger_entity
            prompt.conditional_state.musician_entity = MusicEntity(pref_label=trigger_entity.common_name, wiki_entity=trigger_entity)
            prompt.conditional_state.discussed_entities.append(trigger_entity)
            prompt.conditional_state.asked_question = 'QuestionLikedMusicianTemplate' # This is the handler function for the question we are asking.
            prompt.conditional_state.acknowledged_entity = True
            acknowledgment = random.choice(['', self.choose(ACKNOWLEDGE_MENTIONED_MUSICIAN)])
            question = self.choose(QUESTION_DO_YOU_LIKE)
            response = "{} {}".format(acknowledgment, question)
            prompt.text = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, trigger_entity.common_name)
            return prompt

        # Generic response.
        if question_candidates:
            prompt.priority = PromptType.GENERIC
            prompt.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.MUSICIAN)
            prompt.expected_type = WikiEntityInterface.EntityGroup.MUSICIAN
            question_name = random.choice(question_candidates)
            prompt.conditional_state.asked_question = question_name
            question = self.construct_response_from_templates(QUESTION_TEMPLATES, question_name, question=True)
            transition = random.choice(NO_ENTITY_TRANSITIONS)
            prompt.text = " ".join((transition, question))
            return prompt

        # Ask a question about a musician we know about.
        if undiscussed_titles:
            selected_title = undiscussed_titles[0]
            cur_entity = WikiEntityInterface.get_by_name(selected_title)
            if cur_entity:
                prompt.priority = PromptType.GENERIC
                prompt.cur_entity = cur_entity
                prompt.conditional_state.musician_entity = MusicEntity(pref_label=cur_entity.common_name, wiki_entity=cur_entity)
                prompt.conditional_state.discussed_entities.append(cur_entity)
                prompt.conditional_state.asked_question = 'QuestionLikedMusicianTemplate' # This is the handler function for the question we are asking.
                question = self.choose(QUESTION_DO_YOU_LIKE_POPULAR)
                question = Pronoun.replace_pronouns(question, EXAMPLE_MUSICIAN_WIKI_PAGES[selected_title])
                question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, cur_entity.common_name)
                transition = random.choice(ENTITY_TRANSITIONS)
                prompt.text = " ".join((transition, question))
                return prompt

        # We ran out of prompts.
        return None

    def _handle_answer_like_question(self, state, triggered_answers):
        question_name = 'QuestionLikedMusicianTemplate'

        if 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_LIKED_MUSICIAN_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            # Check if the user mentioned a musician.
            musician_wiki_entity = self.state_manager.current_state.entity_linker.best_ent_of_type(
                WikiEntityInterface.EntityGroup.MUSICIAN)
            if state.musician_entity: musician_wiki_entity = state.musician_entity.wiki_entity

            if not musician_wiki_entity and question_name in triggered_answers and 'answer' in triggered_answers[question_name]:
                musician_name = triggered_answers[question_name]['answer']
                musician_wiki_entity = WikiEntityInterface.link_span(musician_name)

            # If we know the musician.
            if musician_wiki_entity and WikiEntityInterface.is_in_entity_group(musician_wiki_entity, WikiEntityInterface.EntityGroup.MUSICIAN):
                if state.acknowledged_entity:
                    response = self.choose(ACKNOWLEDGE_LIKED_MUSICIAN)
                else:
                    response = self.choose(ACKNOWLEDGE_MENTIONED_MUSICIAN)
                response = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, musician_wiki_entity.common_name)
                rg_result = self.prepare_rg_result(response, state)
                rg_result.conditional_state.discussed_entities.append(musician_wiki_entity)
                musician_entity = MusicEntity(pref_label=musician_wiki_entity.common_name, wiki_entity=musician_wiki_entity)
                song_entity = self.get_song_of_musician(musician_entity, state.discussed_entities)
                if song_entity:
                    expression = self.choose(EXPRESS_INTEREST_OTHER_SONG)
                    expression = expression.replace(f"SONG_{WikiEntityInterface.ENTITY_PLACEHOLDER}", song_entity.pref_label)
                    expression = expression.replace(f"MUSICIAN_{WikiEntityInterface.ENTITY_PLACEHOLDER}", musician_entity.pref_label)
                    question = self.choose(QUESTION_OTHER_SONGS)
                    question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, musician_entity.pref_label)
                    rg_result.text = f"{response} {expression} {question}"
                    rg_result.cur_entity = song_entity.wiki_entity
                    rg_result.conditional_state.needs_internal_prompt = False
                    rg_result.conditional_state.next_treelet = self.name
                    rg_result.conditional_state.asked_question = 'QuestionWhichOfTheirSongsDoYouLike'
            elif state.num_repeats < REPEAT_THRESHOLD:
                response = self.choose(QUESTION_COULD_YOU_REPEAT)
                rg_result = self.prepare_rg_result(response, state)
                rg_result.conditional_state.repeated_question = True
                rg_result.conditional_state.needs_internal_prompt = False
                rg_result.conditional_state.next_treelet = self.name
                rg_result.conditional_state.asked_question = 'QuestionLikedMusicianTemplate'
            else:
                response = self.choose(ACKNOWLEDGE_COULDNT_GET_MUSICIAN)
                rg_result = self.prepare_rg_result(response, state)
                rg_result.priority = ResponsePriority.WEAK_CONTINUE
                rg_result.conditional_state.needs_internal_prompt = False

        return rg_result

    def _handle_answer_liked_songs(self, state, triggered_templates):
        question_name = 'QuestionWhichOfTheirSongsDoYouLike'
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        current_state = self.state_manager.current_state
        user_initiated = current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state)

        if cur_entity and user_initiated and WikiEntityInterface.is_in_entity_group(cur_entity, WikiEntityInterface.EntityGroup.SONG):
            response = self.choose(ACKNOWLEDGE_LIKED_SONGS)
            rg_result = self.prepare_rg_result(response, state)
        else:
            response = self.choose(ACKNOWLEDGE_LIKED_SONGS_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True

        return rg_result

    def _handle_question_like(self, state, triggered_templates):
        response = self.choose(MANY_RESPONSES)
        rg_result = self.prepare_rg_result(response, state)
        return rg_result

    def _handle_expression_chat_musician(self, state, triggered_templates):
        expression_name = 'ChatMusician'
        response = self.choose(CHAT_MUSICIAN_EXPRESSIONS)
        rg_result = self.prepare_rg_result(response, state)
        #rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.INSTRUMENT)
        return rg_result

    @staticmethod
    def get_musician(song_name):

        # Try to find the musician from the Wiki overview.
        musician_name = WikiEntityInterface.extract_musician_name_from_song_overview(song_name)

        if musician_name:
            wiki_entity = WikiEntityInterface.link_span(musician_name)
            if wiki_entity and WikiEntityInterface.is_in_entity_group(wiki_entity, WikiEntityInterface.EntityGroup.MUSICIAN):
                musician_entity = MusicEntity(pref_label=wiki_entity.common_name, wiki_entity=wiki_entity)
                return musician_entity

        # Try to find in Knowledge graph
        musician_entity = KnowledgeInterface().get_musician_entity_by_song(song_name)
        return musician_entity

    @staticmethod
    def get_song_of_musician(musician_entity, blacklist=[]):
        musician_name = musician_entity.pref_label
        song_entity = KnowledgeInterface().get_song_entity_by_musician(musician_name)
        return song_entity