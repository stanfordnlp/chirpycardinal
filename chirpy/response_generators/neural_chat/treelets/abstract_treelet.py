import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

from chirpy.annotators.gpt2ed import GPT2ED
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, ResponsePriority, PromptResult, PromptType, emptyResult, emptyResult_with_conditional_state, emptyPrompt
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.response_generators.neural_chat.state import State, ConditionalState, UserLabel, BotLabel
from chirpy.response_generators.neural_helpers import neural_response_filtering
from chirpy.response_generators.neural_chat.util import MAX_NUM_GPT2ED_TURNS, GPT2ED_DECODE_CONFIG, is_two_part, question_part
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.regex.regex_template import RegexTemplate, oneof
from chirpy.core.util import remove_punc, get_ngrams
from chirpy.core.regex.util import NONEMPTY_TEXT, OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID, oneof, one_or_more_spacesep
from chirpy.core.entity_linker.entity_groups import EntityGroup

logger = logging.getLogger('chirpylogger')

NEGNAV_RESPONSE_HANDOVER = "OK, no problem."

YOU_WORDS = ['you', 'yours', "your's", 'your']

RETURN_QUESTION_PHRASES = [
    "(how|what)('s)?" + OPTIONAL_TEXT_MID + oneof(YOU_WORDS),
    'and you$',
]

class ReturnQuestionTemplate(RegexTemplate):
    slots = {
        'return_question_phrase': RETURN_QUESTION_PHRASES,
    }
    templates = [
        OPTIONAL_TEXT_PRE + "{return_question_phrase}" + OPTIONAL_TEXT_POST,
    ]
    positive_examples = [
        ("i don't know what about you", {'return_question_phrase': 'what about you'}),
        ("what are you doing right now", {'return_question_phrase': 'what are you'}),
        ("how's yours going", {'return_question_phrase': "how's yours"}),
        ("it's nice actually how about yours", {'return_question_phrase': 'how about yours'}),
        ("not bad and you", {'return_question_phrase': 'and you'}),
    ]
    negative_examples = [
        "we stayed home",
        "do you like horses",
        "i'm talking to you",
        "me and you are talking",
    ]

class Treelet(ABC):

    def __init__(self, rg):
        self.state_manager = rg.state_manager

    @property
    def name(self):
        return type(self).__name__

    def __repr__(self):
        return f"<Treelet: {self.name}>"

    @property
    def launch_appropriate(self) -> bool:
        if hasattr(self, '_launch_appropriate'):
            return self._launch_appropriate
        else:
            raise NotImplementedError(f'{self.name} does not have a _launch_appropriate flag')

    @property
    def starter_question_expected_type(self) -> Optional[EntityGroup]:
        """Returns the expected_type of the starter question"""
        if hasattr(self, '_starter_question_expected_type'):
            expected_type = self._starter_question_expected_type
            logger.info(f"{self.name} has starter_question_expected_type={expected_type}")
            return expected_type
        else:
            return None

    def update_state(self, state: State):
        """
        This function is run for each treelet on every turn (before getting response).
        It can be used to update the state based on "listening in" to the conversation, even if the treelet isn't
        going to produce a response on this turn.
        """
        pass

    def get_starter_question_and_labels(self, state: State, for_response: bool = False, for_launch: bool = False) -> Tuple[Optional[str], List[str]]:
        """
        Inputs:
            for_response: if True, the provided starter question will be used to make a response. Otherwise, used to make a prompt.
            for_launch: if True, the provided starter question will be used as part of launch sequence.

        Returns a tuple of:
            - A starter question (str), or None (if it's not appropriate for this treelet to ask a starter question at this time).
            - Labels for the starter question, that should go in the state.
            - priority: ResponsePriority or PromptType
        """
        raise NotImplementedError()

    def user_asking_return_question(self, history) -> bool:
        """Returns True iff the user is asking the "return question" to the starter question"""
        return ReturnQuestionTemplate().execute(history[-1]) is not None

    @property
    def return_question_answer(self) -> str:
        """Gives a response to the user if they ask the "return question" to our starter question"""
        raise NotImplementedError()

    @property
    def use_neg_answer_as_negnav(self) -> bool:
        """If True, after asking starter question, interpret a negative answer as negnav"""
        if hasattr(self, '_use_neg_answer_as_negnav'):
            return self._use_neg_answer_as_negnav
        else:
            return False

    def optionally_quit_conv(self, state: State) -> Optional[ResponseGeneratorResult]:
        """
        If we should quit the conversation instead of getting a gpt2ed response, returns a
        ResponseGeneratorResult, otherwise gives None.
        """
        user_utterance = self.state_manager.current_state.text
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity
        nav_intent = self.state_manager.current_state.navigational_intent

        # If the user has given a posnav intent (for something other than the current topic), quit without saying anything
        if nav_intent.pos_intent and not nav_intent.pos_topic_is_current_topic:
            logger.primary_info(f'User has PosNav intent for something other than the current topic, so Neural Chat {self.name} is stopping talking')
            return emptyResult_with_conditional_state(state, ConditionalState(None, self.name, user_utterance, [UserLabel.POS_NAV]))

        # If the user is giving negnav intent, acknowledge and handoff
        if nav_intent.neg_intent or (self.use_neg_answer_as_negnav and self.state_manager.current_state.dialog_act['is_no_answer']):
            logger.primary_info(f'User has NegNav intent (or possibly neg answer), so giving handover response with needs_prompt=True.')
            return ResponseGeneratorResult(text=NEGNAV_RESPONSE_HANDOVER, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=cur_entity,
                                           conditional_state=ConditionalState(None, self.name, user_utterance, [UserLabel.NEG_NAV], NEGNAV_RESPONSE_HANDOVER, [BotLabel.HANDOVER]))
        return None

    def get_fallback_response(self, state: State, history: List[str]) -> str:
        """
        Give a response (that doesn't use GPT2ED) that ends this conversation with needs_prompt=True.
        This is used if
            (a) there's a problem with GPT2ED
            (b) the user's utterance is offensive, so we don't want GPT2ED to respond
            (c) at the end of the conversation as a wrapup phrase
        """
        if hasattr(self, 'fallback_response'):
            return self.fallback_response
        else:
            raise NotImplementedError(f'{self.name} does not have a fallback_response')

    def get_history(self, state: State) -> List[str]:
        """
        Get the history of the conversation so far.
        Returns an odd-length list of strings, starting and ending with user utterances.
        """
        conv_history = state.conv_histories[self.name]  # ConvHistory
        utterance_history = conv_history.utterances
        assert len(utterance_history) % 2 == 0, "utterance_history should be even length"
        user_utterance = self.state_manager.current_state.text
        return utterance_history + [user_utterance]

    def optionally_get_nonneural_response(self, history: List[str]):
        """
        If we should give a non-neural response instead of calling GPT2ED, give the response here.

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances

        Returns:
            non_neural_response: str or None.
            user_labels: any additional labels that should be applied to the user utterance on this turn
            bot_labels: any additional labels that should be applied to the bot utterance on this turn
        """
        return None, [], []

    def edit_history_for_gpt2ed(self, history: List[str]) -> List[str]:
        """
        Returns the history as it should be given as input to GPT2ED

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances, as it exists in the
                neuralchat state.

        Returns:
            new_history: odd-length list of strings, starting and ending with user utterances, as it should be fed to gpt2ed
        """
        assert len(history) % 2 == 1

        new_history = [r for r in history]

        # Only use the part of the starter question which is the actual question (if there is an actual question)
        if history[0] == '' and len(history) >= 2:
            question_part_only = question_part(history[1])
            if question_part_only:
                new_history[1] = question_part_only

        return new_history


    def get_gpt2ed_responses(self, history: List[str]) -> List[str]:
        """
        Sends history to GPT2ED and returns responses.
        """
        gpt2ed_module = GPT2ED(self.state_manager)
        msg = {'history': self.edit_history_for_gpt2ed(history), 'config': GPT2ED_DECODE_CONFIG}
        responses = gpt2ed_module.execute(msg)  # list. will be empty if there was a problem. all responses are guaranteed to end in a sentence-ending token.
        return responses


    def filter_repetition(self, responses: List[str], history: List[str]) -> List[str]:
        """
        Filter out responses in responses which are repetitive (i.e. similar to previous bot utterances in the history).

        @param responses: list of strings. responses from GPT2ED. Can assume all end in sentence-ending tokens.
        @param history: list of strings. the GPT2ED conversation so far, starting with first user utterance, and ending
            with user's most recent utterance.
        @return responses, with repetitive ones filtered out
        """
        assert len(history) % 2 == 1
        prev_bot_utterances = [history[i].lower() for i in range(1, len(history), 2)]  # lowercased
        prev_asked_questions = [question_part(r) for r in prev_bot_utterances]  # list of str/None, lowercased
        prev_asked_questions = [q for q in prev_asked_questions if q]  # list of str
        prev_bot_utterances_nopunc = [remove_punc(s) for s in prev_bot_utterances] # lowercased
        prev_bot_trigrams = {trigram for r in prev_bot_utterances_nopunc for trigram in get_ngrams(r, 3)}  # set

        # Get filtered_responses
        filtered_responses = []
        for response in responses:
            response_nopunc = remove_punc(response).lower()

            # If this utterance has been said before, remove
            if response_nopunc in prev_bot_utterances_nopunc:
                logger.info(f'Removing neural response "{response}" from candidates because we have said it before')
                continue

            # If this utterance has any 3-grams in common with a previous bot utterance, remove
            trigrams = set(get_ngrams(response_nopunc, 3))
            repeated_trigrams = trigrams.intersection(prev_bot_trigrams)
            if repeated_trigrams:
                logger.info(f'Removing neural response "{response}" from candidates because it contains trigrams we have said before: {repeated_trigrams}')
                continue

            # If the question part of this utterance has been said before, remove
            response_question_part = question_part(response)  # str or None
            if response_question_part and any(response_question_part.lower() in q for q in prev_asked_questions):
                logger.info(f'Removing neural response "{response}" from candidates because we have said the question part "{response_question_part}" before')
                continue

            filtered_responses.append(response)

        return filtered_responses


    def choose_best_gpt2_response(self, responses: List[str], history: List[str], state: State) -> Tuple[Optional[str], List[str]]:
        """
        @param responses: list of strings. responses from GPT2ED. Can assume all end in sentence-ending tokens.
        @param history: list of strings. the GPT2ED conversation so far, starting with first user utterance, and ending
            with user's most recent utterance.
        @return: best_response: string, or None if there was nothing suitable.
        @return: bot_labels: list of strings. labels that should be applied to bot utterance
        """
        num_questions = len([response for response in responses if '?' in response])
        enough_questions = num_questions >= len(responses)/3  # need a third questions
        logger.primary_info(f'Of the {len(responses)} GPT2ED responses, {num_questions} are questions, so enough_questions={enough_questions}')

        # Filter out advice/offensive
        responses = neural_response_filtering(responses)

        # Filter out repetitive responses
        responses = self.filter_repetition(responses, history)

        if len(responses) == 0:
            logger.warning('There are 0 suitable GPT2ED responses')
            best_response = None
        else:
            responses = sorted(responses,
                               key=lambda response: (  # all these keys should be things where higher is good
                                   # on first turn, prefer questions. otherwise, condition on enough_questions
                                   ('?' in response) if enough_questions or len(history) <= 3 else ('?' not in response),
                                   is_two_part(response),
                                   len(response),
                               ),
                               reverse=True)

            logger.primary_info('Remaining GPT2ED responses, sorted by preference:\n{}'.format("\n".join(responses)))
            best_response = responses[0]

        # Get bot labels
        bot_labels = []
        if best_response is None:
            bot_labels += [BotLabel.TECH_ERROR, BotLabel.HANDOVER]
        else:
            bot_labels.append(BotLabel.GPT2ED)
            if self.should_stop(best_response, state):
                bot_labels.append(BotLabel.HANDOVER)

        return best_response, bot_labels

    def should_stop(self, bot_response: str, state: State) -> bool:
        """
        Determines whether we should end the GPT2ED conversation on this turn with needs_prompt=True, after giving
        this bot_response
        """
        if '?' not in bot_response:
            logger.primary_info(f'The GPT2ED response does not contain a question, so ending {self.name} conversation.')
            return True
        elif (len(state.conv_histories[self.name].utterances) + 2) / 2 >= MAX_NUM_GPT2ED_TURNS:
            logger.primary_info(f'We have exceeded the max num GPT2ED turns {MAX_NUM_GPT2ED_TURNS}, so leaving {self.name} conversation.')
            return True
        return False

    def get_response(self, state: State) -> ResponseGeneratorResult:
        user_utterance = self.state_manager.current_state.text
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity

        # If we should quit before sending gpt2ed response, do so
        quitting_response = self.optionally_quit_conv(state)
        if quitting_response:
            return quitting_response

        # Get the conversational history
        history = self.get_history(state)

        # If the user's utterance is offensive, use a fallback response to quit the conversation here
        if contains_offensive(user_utterance, 'User utterance "{}" contains offensive phrase "{}"' + f'so using fallback response to quit {self.name} conversation'):
            fallback_response = self.get_fallback_response(state, history)
            return ResponseGeneratorResult(text=fallback_response, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=cur_entity,
                                           conditional_state=ConditionalState(None, self.name, user_utterance, [UserLabel.OFFENSIVE], fallback_response, [BotLabel.FALLBACK]))

        user_labels = []
        bot_labels = []

        # If we should use a non-GPT2ED response on this turn, get it
        non_neural_response, non_neural_response_user_labels, non_neural_response_bot_labels = self.optionally_get_nonneural_response(history)
        if non_neural_response:
            bot_response = non_neural_response
            user_labels += non_neural_response_user_labels
            bot_labels += non_neural_response_bot_labels

        # Otherwise, get GPT2ED responses and choose best one
        else:
            responses = self.get_gpt2ed_responses(history)  # list of strings
            bot_response, gpt2ed_bot_labels = self.choose_best_gpt2_response(responses, history, state)  # str or None
            bot_labels += gpt2ed_bot_labels

        # If the user is asking us the "return question" to our starter question, prepend the return question answer
        # to the bot_response
        if self.user_asking_return_question(history):
            user_labels.append(UserLabel.RETURN_Q)
            if any(self.return_question_answer in h for h in history):
                logger.primary_info(f"{self.name} detected user asking return question, but we've already given the return answer, so letting GPT2ED respond alone")
            else:
                logger.primary_info(f'{self.name} detected user asking return question, so prepending return question answer to GPT2ED response')
                bot_response = "{} Anyway, {}".format(self.return_question_answer, bot_response) if bot_response else self.return_question_answer
                bot_labels.append(BotLabel.RETURN_ANS)

        # If we should end the conversation on this turn, append the fallback phrase as a wrapup phrase.
        # Set needs_prompt=True and next_treelet=None
        if BotLabel.HANDOVER in bot_labels:
            logger.primary_info(f'Bot response has HANDOVER label, so appending fallback response as a wrapup phrase and exiting {self.name} conversation.')
            fallback_response = self.get_fallback_response(state, history)
            if bot_response:
                bot_response = "{} Anyway, {}".format(bot_response, fallback_response)  # use fallback response as a wrapup phrase
            else:
                bot_response = fallback_response
            bot_labels.append(BotLabel.FALLBACK)
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=cur_entity,
                                           conditional_state=ConditionalState(None, self.name, user_utterance, user_labels, bot_response, bot_labels))

        # Otherwise return the response with needs_prompt=False and next_treelet=self
        else:
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=False, state=state, cur_entity=cur_entity,
                                           expected_type=self.starter_question_expected_type,  # also apply expected type to subsequent turns
                                           conditional_state=ConditionalState(self.name, self.name, user_utterance, user_labels, bot_response, bot_labels))

    def get_starter_question_response(self, state: State) -> Optional[ResponseGeneratorResult]:
        """
        If this treelet should give a starter question as a response on this turn, returns the ResponseGeneratorResult
        asking the starter question. Otherwise, returns None
        """
        starter_question, starter_question_labels, priority = self.get_starter_question_and_labels(state, for_response=True)
        if starter_question is None:
            return None
        conditional_state = ConditionalState(self.name, self.name, '', [], starter_question, starter_question_labels)
        return ResponseGeneratorResult(text=starter_question, priority=priority, needs_prompt=False, state=state, cur_entity=None,
                                       conditional_state=conditional_state, expected_type=self.starter_question_expected_type)

    def get_prompt(self, state: State, for_launch: bool = False) -> Optional[PromptResult]:
        """
        If this treelet has a starter question, returns a prompt asking the starter question.
        Otherwise, returns None.

        If for_launch, will give version of starter question that's appropriate for launch sequence.
        """
        starter_question, starter_question_labels, priority = self.get_starter_question_and_labels(state, for_response=False, for_launch=for_launch)
        if starter_question is None:
            return None
        conditional_state = ConditionalState(self.name, self.name, '', [], starter_question, starter_question_labels)
        return PromptResult(text=starter_question, prompt_type=priority, state=state, cur_entity=None,
                            conditional_state=conditional_state, expected_type=self.starter_question_expected_type)

