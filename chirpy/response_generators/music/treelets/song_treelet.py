import random

from chirpy.core.response_priority import ResponsePriority, PromptType

from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_MID, OPTIONAL_TEXT_POST

from chirpy.response_generators.music.utils import logger, WikiEntityInterface, MusicEntity, REPEAT_THRESHOLD

from chirpy.response_generators.music.expression_lists import SURPRISE_EXPRESSIONS, TO_BE, CHAT_CLAUSES, LIKE_CLAUSES, POSITIVE_ADJECTIVES, POSITIVE_ADVERBS, ANSWER_FAVORITE_TEMPLATES, MANY_RESPONSES
from chirpy.response_generators.music.expression_lists import PositiveTemplate, NegativeTemplate, DontKnowTemplate

from chirpy.response_generators.music.treelets.abstract_treelet import Treelet, TreeletType
from chirpy.response_generators.music.treelets.musician_treelet import MusicianTreelet


TRIGGER_PHRASES = [
    'song',
    'songs',
    'track',
    'tracks',
    'single',
    'singles'
]

TRIGGER_ENTITY_GROUPS = [
    WikiEntityInterface.EntityGroup.SONG
]

EXAMPLE_SONG_WIKI_PAGES = [
    #("Rockstar (Post Malone song)", 'id'),
    #("Rain on Me (Lady Gaga and Ariana Grande song)", 'id'),
    #("Blinding Lights", 'id')
]

class QuestionFavoriteSongTemplate(RegexTemplate):
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
        OPTIONAL_TEXT_PRE + "which {trigger_word} do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "which {trigger_word}s do you {like_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what is your all time favorite {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "what is a {trigger_word} that is dear and near to your heart" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ('what is your all time favorite song', {'trigger_word': 'song'}),
        ('which song do you like the most', {'like_word': 'like', 'trigger_word': 'song'}),
        ('what is a song that is dear and near to your heart', {'trigger_word': 'song'})
    ]
    negative_examples = []

class AnswerFavoriteSongTemplate(RegexTemplate):
    slots = {
        'like_word': LIKE_CLAUSES,
        'answer': NONEMPTY_TEXT,
        'trigger_word': TRIGGER_PHRASES,
        'positive_adverb': POSITIVE_ADVERBS,
        'positive_adjective': POSITIVE_ADJECTIVES,
    }
    templates = ANSWER_FAVORITE_TEMPLATES
    positive_examples = [
        ('my favorite song is ENTITY', {'trigger_word': 'song', 'answer': 'ENTITY'}),
    ]
    negative_examples = []

class AnswerWhoseSongTemplate(RegexTemplate):
    slots = {
        'answer': NONEMPTY_TEXT,
        'trigger_word': TRIGGER_PHRASES
    }
    templates = [
        OPTIONAL_TEXT_PRE + "it(\'s| is) {answer}(|\'|\'s) {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "be {answer}(|\'|\'s) {trigger_word}" + OPTIONAL_TEXT_POST,
        OPTIONAL_TEXT_PRE + "{trigger_word} (by|from) {answer}",
        "{answer}(|\'|\'s) {trigger_word}" + OPTIONAL_TEXT_POST,
        "{answer}(|\'|\'s)"
    ]
    positive_examples = [
        ('it is michael jackson\'s song', {'trigger_word': 'song', 'answer': 'michael jackson'}),
    ]
    negative_examples = []

QUESTION_TEMPLATES = {
    'QuestionFavoriteSongTemplate': QuestionFavoriteSongTemplate()
}

ANSWER_TEMPLATES = {
    'QuestionFavoriteSongTemplate': AnswerFavoriteSongTemplate(),
    'QuestionWhoseSong': AnswerWhoseSongTemplate()
}

SENTIMENT_TEMPLATES = {
    'PositiveTemplate': PositiveTemplate(),
    'NegativeTemplate': NegativeTemplate(),
    'DontKnowTemplate': DontKnowTemplate()
}

ACKNOWLEDGE_FAVORITE_SONG = [
    "Oh, ENTITY is a good one!",
    "I have listened to ENTITY before, and I loved it!",
    "I have listened to ENTITY before, it is one of my favorites!"
]

QUESTION_DO_YOU_LIKE = [
    "Do you like it?",
    "Do you listen to ENTITY often?",
    "Is ENTITY a special song for you?",
    "Is ENTITY one of those songs that you listen to over and over again?"
]

QUESTION_DO_YOU_LIKE_POPULAR = [
    "ENTITY has been pretty popular lately. What do you think about it?",
    "I know ENTITY was climbing the charts lately. Have you had a chance to listen to it? Did you like it?",
    "Everyone is crazy about ENTITY nowadays. Is it a song you like too?",
    "A good number of my bot friends recommended that I listen to ENTITY. I guess it is so popular right now. Do you like it?"
]

QUESTION_WHOSE_SONG = [
    "Hmm, whose song was ENTITY?",
    "My memory is giving me a hard time, whose song was ENTITY?",
    "Hmm, I am pretty sure I knew whose song this was, but I cannot recall right now. Whose song was it?"
]

QUESTION_OTHER_SONG = [
    "I have also listened to SONG_ENTITY by MUSICIAN_ENTITY. Do you like that one too?",
    "MUSICIAN_ENTITY had another popular song, SONG_ENTITY. Have you listened to that one?",
    "I heard that SONG_ENTITY by MUSICIAN_ENTITY was also quite popular. What do you think about that one?",
    "Have you heard of SONG_ENTITY by MUSICIAN_ENTITY? It was also pretty popular."
]

QUESTION_COULD_YOU_REPEAT = [
    "Hmm, I couldn\'t get the song you mentioned. Would you mind repeating it?",
    "I\'m having trouble understanding the song you mentioned. Could you repeat it?",
    "Ah, sorry, what is the song name again?",
    "Oops! I couldn't hear you well. What was the name of the song?"
]

ACKNOWLEDGE_COULDNT_GET_SONG = [
    "My apologies, I\'m still having a hard time catching which song you mentioned. Let\'s chat about something else.",
    "Hmm, looks like I\'m having a trouble again. Maybe we should chat about something else.",
    "My ears are giving me a hard time. How about we chat about something else?"
]

ACKNOWLEDGE_COULDNT_GET_MUSICIAN = [
    "Ah, I couldn't recognize the musician. Let\'s see what else we can chat about.",
    "I am having trouble catching the musicians name. Let\'s chat about something else.",
    "Looks like I couldn\'t recognize the musician name. Maybe we should talk about something else."
]

QUESTION_WHY_DO_YOU_LIKE = [
    "Why do you like it so much?",
    "What makes you like it?",
    "What makes you like it so much?"
]

ACKNOWLEDGE_WHOSE_SONG = [
    "Thank you for reminding me!",
    "Ah, how could I forget, thank you for reminding!",
    "Oh, I knew it, thank you so much for the reminder.",
    "Oh, who else could it be? Thank you so much for reminding me again."
]

ACKNOWLEDGE_FAVORITE_SONG_NEGATIVE = [
    "Oh, got it!",
    "Okay!",
    "Sounds good!",
    "I see."
]

ACKNOWLEDGE_FAVORITE_SONG_WHY_DO_YOU_LIKE = [
    "That is a song that I like too!",
    "I am a big fan of it too.",
    "I enjoy listening to it a lot as well.",
    "I'm also a big fan of it."
]

ACKNOWLEDGE_FAVORITE_SONG_WHY_DO_YOU_LIKE_NEGATIVE = ACKNOWLEDGE_FAVORITE_SONG_NEGATIVE

ACKNOWLEDGE_FAVORITE_SONG_ANOTHER_SONG_NEGATIVE = ACKNOWLEDGE_FAVORITE_SONG_NEGATIVE

ACKNOWLEDGE_FAVORITE_SONG_ANOTHER_SONG_POSITIVE = [
    "This song always gets me too, there isn't a thing I would change about it.",
    "Me too, I cannot stop listening to this one, it is definitely one of my favorites.",
    "I love this one, I put it on and start dancing like crazy.",
    "For a while this was the only song I listened, I just wouldn\'t get bored of it."
]

CHAT_SONG_EXPRESSIONS = [
    "I enjoy talking about music a lot!",
    "I love chatting about songs! I love anything related to music!",
    "I love chatting about anything related to music!"
]

ACKNOWLEDGE_MENTIONED_SONG = [
    "ENTITY was stuck in my head for a while!",
    "ENTITY is pretty popular among my bot friends!",
    "ENTITY is in my playlist!",
    "I like singing ENTITY in the shower!"
]

NO_ENTITY_TRANSITIONS = [
    "There was something I wanted your help with. I have a song stuck in my head and I need something new to listen to.",
    "I'm working on a playlist and I want to find some new songs for it. ",
    "I'm always interested to hear what kind of music people like. ",
]

ENTITY_TRANSITIONS = [
    "A lot of people have been talking to me about music and ",
    "I've been hearing about some new songs and I'd love to get your opinion. ",
    "I wanted to ask you about some new music. "
]

class SongTreelet(Treelet):

    def __init__(self, rg):
        super().__init__(rg)
        self.name = "song"
        self.repr = "Song Treelet"
        self.can_prompt = True
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
        if state.last_turn_asked_question == 'QuestionFavoriteSongTemplate':
            response = self._handle_answer_favorite_question(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionWhyDoYouLikeSong':
            response = self._handle_answer_favorite_question_why_do_you_like(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionWhoseSong':
            response = self._handle_answer_whose_song(state, triggered_answers)
        elif state.last_turn_asked_question == 'QuestionAnotherSongOfMusician':
            response = self._handle_answer_favorite_question_another_song(state, triggered_answers)
        else:
            # Last turn was a question, but we don't have a matching template. This should not have happened.
            error_message = "Last turn question {} is not a part of {}. This is not supposed to happen.".format(state.last_turn_asked_question, self.name)
            logger.error(error_message)
            response = self.get_handoff_response(self.state_manager, state)
        return response

    def get_response_trigger_entity(self, state, trigger_entity):
        acknowledgment = self.choose(ACKNOWLEDGE_MENTIONED_SONG)
        question = self.choose(QUESTION_DO_YOU_LIKE)
        response = "{} {}".format(acknowledgment, question)
        response = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, trigger_entity.common_name)
        rg_result = self.prepare_rg_result(response, state, cur_entity=trigger_entity)

        musician_entity = MusicianTreelet.get_musician(trigger_entity.name)
        song_entity = MusicEntity(pref_label=trigger_entity.common_name, wiki_entity=trigger_entity)

        rg_result.conditional_state.song_entity = song_entity
        rg_result.conditional_state.musician_entity = musician_entity
        rg_result.conditional_state.discussed_entities.append(trigger_entity)
        rg_result.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong'  # This is the handler function for the question we are asking.
        rg_result.conditional_state.next_treelet = self.name
        rg_result.conditional_state.needs_internal_prompt = False
        return rg_result

    def get_response_trigger_phrase(self, state, trigger_phrase = None):
        utterance = self.state_manager.current_state.text
        triggered_templates = self.process_templates(QUESTION_TEMPLATES, utterance)
        sentiment_answers = self.process_templates(SENTIMENT_TEMPLATES, utterance)
        triggered_templates = {**triggered_templates, **sentiment_answers}
        undiscussed_items = [title for title in EXAMPLE_SONG_WIKI_PAGES if
                              not WikiEntityInterface.is_title_in_entities(title, state.discussed_entities)]
        trigger_entity = None
        if trigger_phrase:
            trigger_entity = WikiEntityInterface.link_span(trigger_phrase)
            if trigger_entity and not WikiEntityInterface.is_in_entity_group(trigger_entity, WikiEntityInterface.EntityGroup.SONG):
                trigger_entity = None

        response = None
        if 'QuestionFavoriteSongTemplate' in triggered_templates:
            response = self._handle_question_favorite(state, triggered_templates)
        elif trigger_entity:
            response = self.get_response_trigger_entity(state, trigger_entity)
        elif undiscussed_items:
            song_title, song_kid = undiscussed_items[0]
            cur_entity = WikiEntityInterface.get_by_name(song_title)
            if cur_entity:
                question = self.choose(QUESTION_DO_YOU_LIKE_POPULAR)
                question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, cur_entity.common_name)
                response = self.prepare_rg_result(question, state, cur_entity=cur_entity)
                response.conditional_state.song_entity = MusicEntity(pref_label=cur_entity.common_name, wiki_entity=cur_entity,
                                          kid=song_kid)
                response.conditional_state.discussed_entities.append(cur_entity)
                response.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong' # This is the handler function for the question we are asking.
                response.conditional_state.next_treelet = self.name
                response.conditional_state.needs_internal_prompt = False

        if not response:
            response = self._handle_expression_chat_song(state, None)

        return response

    def get_prompt(self, state, conditional_state=None, trigger_entity = None):
        question_candidates = [q for q in list(QUESTION_TEMPLATES.keys()) if q not in state.asked_questions]
        is_correct_entity_group = trigger_entity and WikiEntityInterface.is_in_entity_group(trigger_entity, WikiEntityInterface.EntityGroup.SONG)
        undiscussed_items = [title for title in EXAMPLE_SONG_WIKI_PAGES if
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
            song_entity = MusicEntity(pref_label=trigger_entity.common_name, wiki_entity=trigger_entity)
            prompt.conditional_state.song_entity = song_entity

            prompt.priority = PromptType.CURRENT_TOPIC
            prompt.cur_entity = trigger_entity
            prompt.conditional_state.discussed_entities.append(trigger_entity)
            prompt.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong' # This is the handler function for the question we are asking.

            acknowledgment = self.choose(ACKNOWLEDGE_MENTIONED_SONG)
            question = self.choose(QUESTION_DO_YOU_LIKE)
            response = "{} {}".format(acknowledgment, question)
            prompt.text = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, trigger_entity.common_name)
            return prompt

        # Generic response.
        # if question_candidates:
        #     prompt.priority = PromptType.GENERIC
        #     prompt.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.SONG)
        #     prompt.expected_type = WikiEntityInterface.EntityGroup.SONG
        #     question_name = self.choose(question_candidates)
        #     prompt.conditional_state.asked_question = question_name
        #     prompt.text = self.construct_response_from_templates(QUESTION_TEMPLATES, question_name, question=True)
        #     return prompt

        # Ask a question about a song we know about.
        if undiscussed_items:
            song_title, song_kid = undiscussed_items[0]
            cur_entity = WikiEntityInterface.get_by_name(song_title)
            if cur_entity:
                song_entity = MusicEntity(pref_label=cur_entity.common_name, wiki_entity=cur_entity, kid=song_kid)
                prompt.priority = PromptType.GENERIC
                prompt.cur_entity = cur_entity
                prompt.conditional_state.song_entity = song_entity
                prompt.conditional_state.discussed_entities.append(cur_entity)
                prompt.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong' # This is the handler function for the question we are asking.
                question = self.choose(QUESTION_DO_YOU_LIKE_POPULAR)
                question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, cur_entity.common_name)
                transition = random.choice(ENTITY_TRANSITIONS)
                prompt.text = " ".join((transition, question))
                return prompt

        # We ran out of prompts.
        return None

    def _handle_answer_favorite_question(self, state, triggered_answers):
        question_name = 'QuestionFavoriteSongTemplate'

        # Prepare responses
        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers or 'DontKnowTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            # Check if the user mentioned a song.
            song_wiki_entity = None

            if not song_wiki_entity and question_name in triggered_answers and 'answer' in triggered_answers[question_name]:
                song_name = triggered_answers[question_name]['answer']
                song_wiki_entity = WikiEntityInterface.link_span(song_name)

            # If the user mentioned a song, ask a follow up question.
            if song_wiki_entity and WikiEntityInterface.is_in_entity_group(song_wiki_entity, WikiEntityInterface.EntityGroup.SONG):
                response = self.choose(ACKNOWLEDGE_FAVORITE_SONG)
                followup = self.choose(QUESTION_WHY_DO_YOU_LIKE)
                response = "{} {}".format(response, followup)
                rg_result = self.prepare_rg_result(response, state)

                song_entity = MusicEntity(pref_label=song_wiki_entity.common_name, wiki_entity=song_wiki_entity)
                musician_entity = MusicianTreelet.get_musician(song_wiki_entity.name)

                rg_result.conditional_state.song_entity = song_entity
                rg_result.conditional_state.musician_entity = musician_entity
                rg_result.text = response.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, song_wiki_entity.common_name)
                rg_result.cur_entity = song_wiki_entity
                rg_result.conditional_state.discussed_entities.append(song_wiki_entity)
                rg_result.conditional_state.needs_internal_prompt = False
                rg_result.conditional_state.next_treelet = self.name
                rg_result.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong'
            # We don't know which song the user mentioned.
            elif state.num_repeats < REPEAT_THRESHOLD:
                response = self.choose(QUESTION_COULD_YOU_REPEAT)
                rg_result = self.prepare_rg_result(response, state)
                rg_result.conditional_state.repeated_question = True
                rg_result.conditional_state.needs_internal_prompt = False
                rg_result.conditional_state.next_treelet = self.name
                rg_result.conditional_state.asked_question = 'QuestionWhyDoYouLikeSong'
            else:
                response = self.choose(ACKNOWLEDGE_COULDNT_GET_SONG)
                rg_result = self.prepare_rg_result(response, state)
                rg_result.conditional_state.needs_internal_prompt = False

        return rg_result

    def _handle_answer_favorite_question_why_do_you_like(self, state, triggered_answers):
        question_name = 'QuestionWhyDoYouLikeSong'
        musician_entity = state.musician_entity
        song_entity = state.song_entity
        if not musician_entity and song_entity:
            musician_entity = MusicianTreelet.get_musician(song_entity.pref_label)

        if self.is_no_answer() or 'NegativeTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_WHY_DO_YOU_LIKE_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True
        else:
            if 'DontKnowTemplate' in triggered_answers:
                response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_WHY_DO_YOU_LIKE_NEGATIVE)
            else:
                response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_WHY_DO_YOU_LIKE)

            # Song is user initiated, but we talked about it before.
            # Check if there is a treelet that can respond to the user initiated cur_entity, if it exists.
            cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
            current_state = self.state_manager.current_state
            user_initiated = current_state.entity_tracker.cur_entity_initiated_by_user_this_turn(current_state)
            if user_initiated and cur_entity and cur_entity  in state.discussed_entities:
                rg_result = self.prepare_rg_result(response, state)
            # We didn't talk about the song before abd we know the musician.
            elif musician_entity:
                rg_result = self.create_rg_result_ask_another_song_of_musician(state, musician_entity)
                if rg_result:
                    rg_result.text = f"{response} {rg_result.text}"
                else:
                    rg_result = self.prepare_rg_result(response, state)
                    rg_result.conditional_state.needs_internal_prompt = False
            else:
                question = self.choose(QUESTION_WHOSE_SONG)
                if song_entity:
                    question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, song_entity.pref_label)
                else:
                    question = question.replace(WikiEntityInterface.ENTITY_PLACEHOLDER, 'that')
                response = f"{response} {question}"
                rg_result = self.prepare_rg_result(response, state)
                rg_result.conditional_state.needs_internal_prompt = False
                rg_result.conditional_state.asked_question = 'QuestionWhoseSong'
                rg_result.conditional_state.next_treelet = self.name
                rg_result.expected_type = WikiEntityInterface.EntityGroup.MUSICIAN

        return rg_result

    def create_rg_result_ask_another_song_of_musician(self, state, musician_entity, conditional_blacklist=[]):
        blacklist = state.discussed_entities + conditional_blacklist
        song_entity = MusicianTreelet.get_song_of_musician(musician_entity, blacklist)
        if song_entity and WikiEntityInterface.is_in_entity_group(song_entity.wiki_entity,
                                                                  WikiEntityInterface.EntityGroup.SONG):
            question = self.choose(QUESTION_OTHER_SONG)
            musician_placeholder = f'MUSICIAN_{WikiEntityInterface.ENTITY_PLACEHOLDER}'
            song_placeholder = f'SONG_{WikiEntityInterface.ENTITY_PLACEHOLDER}'
            question = question.replace(musician_placeholder, musician_entity.pref_label)
            question = question.replace(song_placeholder, song_entity.pref_label)
            rg_result = self.prepare_rg_result(question, state)
            rg_result.conditional_state.discussed_entities = conditional_blacklist + [song_entity.wiki_entity]
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.conditional_state.asked_question = 'QuestionAnotherSongOfMusician'
            rg_result.conditional_state.next_treelet = self.name
            rg_result.conditional_state.discussed_entities.append(song_entity.wiki_entity)
            rg_result.cur_entity = song_entity.wiki_entity
            return rg_result
        return None

    def _handle_answer_whose_song(self, state, triggered_answers):
        question_name = 'QuestionWhoseSong'
        musician_wiki_entity = self.state_manager.current_state.entity_linker.best_ent_of_type(WikiEntityInterface.EntityGroup.MUSICIAN)
        if not musician_wiki_entity or musician_wiki_entity.name is WikiEntityInterface.PageName.MUSICIAN:
            if question_name in triggered_answers and 'answer' in triggered_answers[question_name]:
                musician_name = triggered_answers[question_name]['answer']
                musician_wiki_entity = WikiEntityInterface.link_span(musician_name)

        rg_result = None
        if musician_wiki_entity and WikiEntityInterface.is_in_entity_group(musician_wiki_entity, WikiEntityInterface.EntityGroup.MUSICIAN):
            musician_entity = MusicEntity(pref_label=musician_wiki_entity.common_name, wiki_entity=musician_wiki_entity)
            rg_result = self.create_rg_result_ask_another_song_of_musician(state, musician_entity)
            if rg_result:
                response = self.choose(ACKNOWLEDGE_WHOSE_SONG)
                rg_result.text = f"{response} {rg_result.text}"

        if not rg_result:
            response = self.choose(ACKNOWLEDGE_COULDNT_GET_MUSICIAN)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False

        return rg_result

    def _handle_answer_favorite_question_another_song(self, state, triggered_answers):
        question_name = 'QuestionAnotherSongOfMusician'
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity

        if self.is_yes_answer() or 'YesTemplate' in triggered_answers:
            response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_ANOTHER_SONG_POSITIVE)
            rg_result = self.prepare_rg_result(response, state)
        else:
            response = self.choose(ACKNOWLEDGE_FAVORITE_SONG_ANOTHER_SONG_NEGATIVE)
            rg_result = self.prepare_rg_result(response, state)
            rg_result.conditional_state.needs_internal_prompt = False
            rg_result.needs_prompt = True

        return rg_result

    def _handle_question_favorite(self, state, triggered_templates):
        # Construct our answer from the example answers
        response = self.choose(MANY_RESPONSES)
        rg_result = self.prepare_rg_result(response, state)
        return rg_result

    def _handle_expression_chat_song(self, state, triggered_templates):
        expression_name = 'ChatSong'
        response = self.choose(CHAT_SONG_EXPRESSIONS)
        rg_result = self.prepare_rg_result(response, state)
        rg_result.cur_entity = WikiEntityInterface.get_by_name(WikiEntityInterface.PageName.SONG)
        return rg_result

