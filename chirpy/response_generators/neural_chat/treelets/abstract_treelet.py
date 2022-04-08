import logging
from typing import List, Optional, Tuple
from itertools import takewhile
import random
import re
from concurrent import futures

from chirpy.annotators.blenderbot import BlenderBot
from chirpy.annotators.responseranker import ResponseRanker
from chirpy.core.response_generator.treelet import Treelet as BaseTreelet
from chirpy.core.response_generator_datatypes import ResponsePriority, emptyResult_with_conditional_state
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.response_generators.neural_chat.state import State, ConditionalState, UserLabel, BotLabel
from chirpy.response_generators.neural_fallback.neural_helpers import neural_response_filtering
from chirpy.response_generators.neural_chat.util import MAX_NUM_NEURAL_TURNS, NEURAL_DECODE_CONFIG, is_two_part, question_part, NUM_CONVO_OPENING_TURNS, BLACKLIST, is_short, is_short_set
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.core.regex.regex_template import RegexTemplate
from chirpy.core.util import remove_punc, get_ngrams
from chirpy.core.regex.util import OPTIONAL_TEXT_PRE, OPTIONAL_TEXT_POST, OPTIONAL_TEXT_MID, oneof
from chirpy.core.entity_linker.entity_groups import EntityGroup
from chirpy.core.smooth_handoffs import SmoothHandoff

logger = logging.getLogger('chirpylogger')

NEGNAV_RESPONSE_HANDOVER = "OK, no problem."

YOU_WORDS = ['you', 'yours', "your's", 'your']
WH_WORDS = ['what', 'why', 'who', 'how', 'where', 'when', 'did']

RETURN_QUESTION_PHRASES = [
    "(how|what)('s)?" + OPTIONAL_TEXT_MID + oneof(YOU_WORDS),
    'and you$',
]

ENTITY_BLACK_LIST = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                     'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                     'November', 'December',
                     'Jews', 'Feces', 'Swine', 'Devil',
                     '2019–20 coronavirus outbreak',
                     'Bible', 'Quran', 'Gospel', 'Christianity' #religious texts
                     'HTTP cookie',
                     'Health', 'Business', 'Entertainment', 'Science', 'News', # general stuff from News
                     'Film', 'Labor',
                     'Labor theory of value', #what??
                     'Donald Trump (song)',
                     'Soccer (dog)',
                     'Legacy system', 'Legacy game', 'Left-wing politics', 'Left-right political spectrum', 'Left-libertarianism', 'American Left', 'Working memory',
                     'Gender transitioning'
                     ] # what IS this blacklist and why does it seem....biased?

def remove_parens(s):
    if '(' not in s: return s
    return s[:s.index('(')].strip()

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

class Treelet(BaseTreelet):

    def __init__(self, rg):
        super().__init__(rg)
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
        """Returns True iff the user is asking the "return question" to the starter question

        DEPRECATED
        """
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
        If we should quit the conversation instead of getting a neural response, returns a
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
        if nav_intent.neg_intent or (self.use_neg_answer_as_negnav and self.state_manager.current_state.dialogact['is_no_answer']):
            logger.primary_info(f'User has NegNav intent (or possibly neg answer), so giving handover response with needs_prompt=True.')
            return ResponseGeneratorResult(text=NEGNAV_RESPONSE_HANDOVER, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=cur_entity,
                                           conditional_state=ConditionalState(None, self.name, user_utterance, [UserLabel.NEG_NAV], NEGNAV_RESPONSE_HANDOVER, [BotLabel.HANDOVER]))
        return None

    def get_fallback_response(self, state: State, history: List[str]) -> str:
        """
        Give a response (that doesn't use a neural model) that ends this conversation with needs_prompt=True.
        This is used if
            (a) there's a problem with the neural model
            (b) the user's utterance is offensive, so we don't want neural model to respond
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
        user_utterance = self.state_manager.current_state.text
        try:
            conv_history = state.conv_histories[self.name]  # ConvHistory
            utterance_history = conv_history.utterances
            assert len(utterance_history) % 2 == 0, "utterance_history should be even length"
            return utterance_history + [user_utterance]
        except KeyError:
            return [user_utterance]


    def optionally_get_nonneural_response(self, history: List[str]):
        """
        If we should give a non-neural response instead of calling the neural model, give the response here.

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances

        Returns:
            non_neural_response: str or None.
            user_labels: any additional labels that should be applied to the user utterance on this turn
            bot_labels: any additional labels that should be applied to the bot utterance on this turn
        """
        return None, [], []

    def edit_history_for_remote(self, history: List[str]) -> List[str]:
        """
        Returns the history as it should be given as input to the remote neural module

        Inputs:
            history: odd-length list of strings, starting and ending with user utterances, as it exists in the
                neuralchat state.

        Returns:
            new_history: odd-length list of strings, starting and ending with user utterances, as it should be fed to remote module
        """
        assert len(history) % 2 == 1

        new_history = [r for r in history]

        # Special case for handling start-of-conversation null turn. Here, we only use the part
        # of the starter question which is the actual question (if there is an actual question)
        if history[0] == '' and len(history) >= 2:
            question_part_only = question_part(history[1])
            if question_part_only:
                new_history[1] = question_part_only

        return new_history


    def get_neural_responses(self, history: List[str]) -> List[str]:
        """
        Sends history to neural module (BlenderBot in this case; GPT2ED is also an option) and returns responses.
        """
        # Because we preemptively run neural modules the results of .execute() is actually cached
        # in self.state_manager.current_state.blenderbot. This just returns the cached result.
        if hasattr(self.state_manager.current_state, 'blenderbot'):
            # Sometimes the call to BlenderBot has not yet finished, in which case we store the future
            # in self.state_manager.current_state.blenderbot and retrieve the result here.
            if isinstance(self.state_manager.current_state.blenderbot, futures.Future):
                future_result = self.state_manager.current_state.blenderbot.result()
                # Replace the future with the future's result
                setattr(self.state_manager.current_state, 'blenderbot', future_result)
            responses, scores = self.state_manager.current_state.blenderbot
        else:
            logger.warning("Manual call to BlenderBot in NEURAL_CHAT.")
            neural_module = BlenderBot(self.state_manager)
            responses, scores = neural_module.execute()
        return responses, scores # results (responses, probabilities)


    def filter_repetition(self, responses: List[str], history: List[str], scores: Optional[List[float]] = None) -> List[str]:
        """
        Filter out responses in responses which are repetitive (i.e. similar to previous bot utterances in the history).

        @param responses: list of strings. responses from neural module. Can assume all end
        in sentence-ending tokens.
        @param history: list of strings. the neural chat conversation so far, starting with first
        user utterance, and ending with user's most recent utterpance.
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
        if scores is None:
            used_scores = [0.] * len(responses)
        else:
            used_scores = scores
        for response, score in zip(responses, scores):
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

            if scores is None:
                filtered_responses.append(response)
            else:
                filtered_responses.append((response, score))

        if len(filtered_responses):
            return list(zip(*filtered_responses))
        else:
            return tuple(), tuple()

    def get_response_rankings(self, history: List[str], responses: List[str]):
        neural_module = ResponseRanker(self.state_manager)
        msg = {'responses': responses, 'context': self.edit_history_for_remote(history)}
        scores = neural_module.execute(msg)  # list. will be empty if there was a problem. all responses are guaranteed to end in a sentence-ending token.

        if scores is not None and isinstance(scores,dict) and 'pos' in scores:
            return scores['pos']
        return None

    def is_question(self, response):
        if '?' in response: return True
        if any(response.startswith(q) for q in WH_WORDS): return True
        return False

    def choose_best_neural_response(self, responses: List[str], history: List[str], state: State, scores: Optional[List[float]] = None):
        """
        @param responses: list of strings. responses from neural module, model probability, and ranker score. Can assume all end
        in sentence-ending tokens.
        @param history: list of strings. the neural chat conversation so far, starting with first user
        utterance, and ending with user's most recent utterance.
        @return: best_response: string, or None if there was nothing suitable.
        @return: bot_labels: list of strings. labels that should be applied to bot utterance

        Basic gist: filter out advice-giving/offensive generations, repetitive responses,
        then rank by whether we generated a question (unless there's enough questions); then rank
        by whether the response is two-part, then by length.


        """

        # find num. questions in raw_responses
        num_questions = len([response for response in responses if self.is_question(response)])

        #enough_questions = num_questions >= len(responses)/3  # need a third questions
        #logger.primary_info(f'Of the {len(responses)} neural responses, {num_questions} are questions, so enough_questions={enough_questions}')

        # Jointly filter out (response, score) tuples, or just responses. Scores should be None if we're not using them.
        # Filter out advice/offensive
        logger.primary_info("Got the following responses: {}".format("\n".join([str(x) for x in zip(responses, scores)])))
        responses, scores = neural_response_filtering(responses, scores)
        responses, scores = self.filter_repetition(responses, history, scores)

        if len(responses) == 0:
            logger.warning('There are 0 suitable neural responses')
            best_response = None
        else:
            responses = [self.cutoff_questions(response, state) for response in responses]
            final_response_score_pairs = self.rerank_responses(list(zip(scores, responses)), responses, history, state)
            logger.primary_info('Remaining neural responses with scores after editing, sorted by preference:\n' +
                                "\n".join([str(x) for x in final_response_score_pairs]))
            best_response = final_response_score_pairs[0][1] # best_response, state -> processed version of best_response

        # Get bot labels -- determines what to do next
        bot_labels = []
        if best_response is None: # If the model returned zero responses, hand over and report a technical error.
            bot_labels += [BotLabel.TECH_ERROR, BotLabel.HANDOVER]
        else:
            bot_labels.append(BotLabel.NEURAL)
            if self.is_topic_shifting_question(best_response):
                logger.primary_info("Best response is a topic-shifting question; incrementing by 1.")
                bot_labels.append(BotLabel.TOPIC_SHIFT)
            if self.should_stop(best_response, state):
                bot_labels.append(BotLabel.HANDOVER)

        return best_response, bot_labels, responses

    def should_not_ask_question(self, state, best_response, sentences):
        """Returns True."""
        if self.too_many_turns(state) and self.is_question(best_response): return True
        yeeted = " ".join(takewhile(lambda x: not self.is_question(x), sentences))
        if len(yeeted.split()) < 6: return False
        else: return bool(random.random() < 0.3)

    def is_topic_shifting_question(self, sentence):
        BAD_NGRAMS = ['hobbies', 'out of town', 'do you have any friends', 'what kind of things do you do for fun',
                      'for work', 'for fun', 'this weekend', 'what do you like', 'for a living', 'weekend', 'week',
                      'favorite color', 'what else do you enjoy', 'what other things do you enjoy', 'do you enjoy',
                      'do you have any siblings', 'do you have siblings', 'what else do you do', 'do you read', 'doing anything fun',]
        sentence = sentence.lower()
        if any(b in sentence for b in BAD_NGRAMS):
            return True
        return False

    def cutoff_questions(self, best_response: str, state: State, remove_topic_shifts : bool = True) -> str:
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Za-z])(?<=\.|\?|!)\s", best_response)
        # hack: if it's the last turn, yeet the question out of the utterance if applicable
        #if self.should_not_ask_question(state, best_response, sentences):
        #    best_response = " ".join(takewhile(lambda x: not self.is_question(x), sentences))
        #    logger.primary_info(f'Trimming question out of final neural chat turn, yielding {best_response}')
        #    # TODO: what if the first sentence already has a question? we just give up + give an empty response rn -- does that work?
        #else: # on all other turns, limit the number of questions to one. stop at first question.
        num_questions = 0
        kept_sentences = []

        limit = 1 if not self.too_many_turns(state) else 0 # 1 if (random.random() < 0.7) else 0

        for sentence in sentences:
            if limit != 0 and num_questions >= limit and (not is_short_set(kept_sentences)):
                break
            if self.is_question(sentence):
                num_questions += 1
                if limit == 0 or (self.is_topic_shifting_question(sentence) and remove_topic_shifts):
                    if (not is_short_set(kept_sentences)): # try not to produce an empty sentence ever if possible
                        logger.primary_info(f"Not adding on sentence: {sentence} ({self.is_topic_shifting_question(sentence)})")
                        break
            # alternative method: if num_questions == 2 here, break. This will include one Q + remaining sentences until another Q is hit.
            kept_sentences.append(sentence)
        return " ".join(kept_sentences)

    def is_weird(self, statement):
        statement = statement.lower()
        if any(b in statement for b in BLACKLIST): return True
        return False

    def rerank_responses(self, response_score_pairs: List[Tuple[str, float]], responses: List[str], history: List[str], state: State) -> List[Tuple[str, float]]:
        policy = self.state_manager.current_state.experiments.look_up_experiment_value("gpt2ed_ranking_policy")
        logger.primary_info(f'{len(responses)} suitable responses; retrieving ranking scores using policy "{policy}"')

        # This is the default policy!
        # if policy == "score_only":
            # these should all be things that are better higher
        policies = {
            "non_empty": (lambda pair: pair[1] != ""),
            "is_question_xor_should_stop": (lambda pair: self.is_question(pair[1]) != self.should_stop(pair[1], state)),
            "is_not_weird": (lambda pair: not self.is_weird(pair[1])),
            "likelihood": (lambda pair: pair[0]),
        }
        response_data = [(pair, tuple([policy(pair) for policy in policies.values()])) for pair in response_score_pairs]
        final_response_score_pairs = list(sorted(response_data, key=lambda x: x[1], reverse=True))
        logger.primary_info('Remaining neural responses with scores after editing, sorted by preference:\n' +
                            "\n".join([
                                f"({x[0][0]:.3f}) {x[0][1]} {','.join((key + '=' + str(value)) for key, value in zip(policies.keys(), (x[1])))}"
                                for x in final_response_score_pairs]))
        # elif policy == "senti_score":
        #     pos_score = self.get_response_rankings(history, responses)
        #     if pos_score is None:  #fallback to gpt2ed scoring
        #         final_response_score_pairs = list(sorted(response_score_pairs, key=lambda pair: pair[0], reverse=True))
        #     else:
        #         final_response_score_pairs = list(sorted(list(zip(pos_score, responses)), key=lambda pair: pair[0], reverse=True))
        # else:
        #     # policy == "rules_only"
        #     final_response_score_pairs = sorted(response_score_pairs,
        #                     key=lambda response_info: (  # all these keys should be things where higher is good
        #                         # if we have too many turns, prefer a statement,
        #                         (not self.is_weird(response_info[1])),
        #                         (self.too_many_turns(state) and not self.is_question(response_info[1])),
        #                         # on first turn, prefer questions. otherwise, condition on enough_questions
        #                         (self.is_question(response_info[1]) if (enough_questions or len(history) <= 3) else (not self.is_question(response_info[1]))),
        #                         is_two_part(response_info[1]),
        #                         len(response_info[1]),
        #                     ),
        #                     reverse=True)
        return [f[0] for f in final_response_score_pairs]

    def too_many_turns(self, state):
        if self.name not in state.conv_histories: return False
        return (len(state.conv_histories[self.name].utterances) + 2) / 2 >= MAX_NUM_NEURAL_TURNS

    def should_stop(self, bot_response: str, state: State) -> bool:
        """
        Determines whether we should end the neural conversation on this turn with needs_prompt=True, after giving
        this bot_response. Current conditions: if the max number of
        neural turns has been exceeded.
        """
        # Exiting if neural chat doesn't ask a follow up might be too aggressive/conservative, esp. since blenderbot can handle this much more coherently than GPT
        # if not self.is_question(bot_response):
        #    logger.primary_info(f'The neural response does not contain a question, so ending {self.name} conversation.')
        #    return True
        if self.is_topic_shifting_question(bot_response) and state.num_topic_shifts >= 0:
            logger.primary_info(f"Already encountered {state.num_topic_shifts} topic shifts, so stopping now.")
            return True
        if self.too_many_turns(state):
            logger.primary_info(f'We have exceeded the max num neural turns {MAX_NUM_NEURAL_TURNS}, so leaving {self.name} conversation.')
            return True
        return False

    def has_recommended_wiki_entity(self, state: State):
        """Determines whether WIKI is about to discuss an entity; if so we do a smooth handoff."""
        wiki_rg_state = self.state_manager.current_state.response_generator_states['WIKI']
        recommended_entity = self.state_manager.current_state.entity_tracker.cur_entity
        if recommended_entity:
            if recommended_entity.is_category:
                logger.info(f"Recommended entity {recommended_entity} is a category, not using it for WIKI")
            elif recommended_entity.name in ENTITY_BLACK_LIST or remove_parens(recommended_entity.name) in ENTITY_BLACK_LIST:
                logger.info(f"Recommended entity {recommended_entity} is blacklisted for WIKI")
            elif recommended_entity.name in wiki_rg_state.entity_state and wiki_rg_state.entity_state[recommended_entity.name].finished_talking:
                logger.info(f"Wiki has finished talking about recommended entity {recommended_entity}")
            else:
                logger.primary_info(f"Neural chat handoff: observing recommended entity {recommended_entity}: {recommended_entity.name}. Handing off to WIKI.")
                return recommended_entity

    @property
    def is_handoff(self):
        return (type(self).__name__ == 'FoodTreelet') # TBD: could be adjusted later

    def get_response(self, state: State, force: bool = False) -> ResponseGeneratorResult:
        _, utterance, response_types = self.get_state_utterance_response_types()
        user_utterance = self.state_manager.current_state.text
        cur_entity = self.state_manager.current_state.entity_tracker.cur_entity

        # If we should quit before sending neural response, do so
        quitting_response = self.optionally_quit_conv(state)
        if quitting_response and not force:
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

        # If we should use a non-neural response on this turn, get it
        non_neural_response, non_neural_response_user_labels, non_neural_response_bot_labels = self.optionally_get_nonneural_response(history)
        acceptable_responses = None
        if non_neural_response:
            logger.info("Grabbing non-neural responses.")
            bot_response = non_neural_response
            user_labels += non_neural_response_user_labels
            bot_labels += non_neural_response_bot_labels

        # Otherwise, get neural responses and choose best one
        else:
            logger.info("Grabbing neural responses.")
            neural_responses, scores = self.get_neural_responses(history)  # list of strings
            bot_response, neural_bot_labels, acceptable_responses = self.choose_best_neural_response(neural_responses, history, state, scores)  # str or None
            bot_labels += neural_bot_labels

        # If the user is asking us the "return question" to our starter question, prepend the return question answer
        # to the bot_response
        # if self.user_asking_return_question(history):
        #     user_labels.append(UserLabel.RETURN_Q)
        #     if any(self.return_question_answer in h for h in history):
        #         logger.primary_info(f"{self.name} detected user asking return question, but we've already given the return answer, so letting neural module respond alone")
        #     else:
        #         logger.primary_info(f'{self.name} detected user asking return question, so prepending return question answer to neural module response')
        #         bot_response = "{} Anyway, {}".format(self.return_question_answer, bot_response) if bot_response else self.return_question_answer
        #         bot_labels.append(BotLabel.RETURN_ANS)

        num_topic_shifts = state.num_topic_shifts
        if BotLabel.TOPIC_SHIFT in bot_labels:
            num_topic_shifts += 1

        # If we should end the conversation on this turn, append the fallback phrase as a wrapup phrase.
        # Set needs_prompt=True and next_treelet=None
        if BotLabel.HANDOVER in bot_labels:
            smooth_handoff = None
            logger.primary_info(f'Bot response has HANDOVER label, so appending fallback response as a wrapup phrase and exiting {self.name} conversation.')
            fallback_response = self.get_fallback_response(state, history)
            if bot_response:
                if self.has_recommended_wiki_entity(state):
                    bot_response = bot_response # We don't need to wrap up, because smooth transition out to WIKI.
                    smooth_handoff = SmoothHandoff.NEURALCHAT_TO_WIKI
                else:
                    bot_response = "{} Anyway, {}".format(bot_response, fallback_response)  # use fallback response as a wrapup phrase
            else:
                bot_response = fallback_response
                bot_labels.append(BotLabel.FALLBACK)
            return ResponseGeneratorResult(text=bot_response, priority=ResponsePriority.STRONG_CONTINUE,
                                           needs_prompt=True, state=state, cur_entity=cur_entity,
                                           conditional_state=ConditionalState(None, self.name, user_utterance, user_labels, bot_response, bot_labels, acceptable_responses, 0),
                                           smooth_handoff=smooth_handoff)

        # Otherwise return the response with needs_prompt=False and next_treelet=self
        else:
            priority = ResponsePriority.CAN_START if self.is_handoff else ResponsePriority.STRONG_CONTINUE

            return ResponseGeneratorResult(text=bot_response, priority=priority,
                                           needs_prompt=False, state=state, cur_entity=cur_entity,
                                           expected_type=self.starter_question_expected_type,  # also apply expected type to subsequent turns
                                           conditional_state=ConditionalState(self.name, self.name, user_utterance, user_labels, bot_response, bot_labels, acceptable_responses, num_topic_shifts))

    # def get_starter_question_response(self, state: State) -> Optional[ResponseGeneratorResult]:
    #     """
    #     NOTE: Not being used.
    #     If this treelet should give a starter question as a response on this turn, returns the ResponseGeneratorResult
    #     asking the starter question. Otherwise, returns None
    #     """
    #     starter_question, starter_question_labels, priority = self.get_starter_question_and_labels(state, for_response=True)
    #     if starter_question is None:
    #         return None
    #     conditional_state = ConditionalState(self.name, self.name, '', [], starter_question, starter_question_labels)
    #     return ResponseGeneratorResult(text=starter_question, priority=priority, needs_prompt=False, state=state, cur_entity=None,
    #                                    conditional_state=conditional_state, expected_type=self.starter_question_expected_type)

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
                            conditional_state=conditional_state, expected_type=self.starter_question_expected_type,
                            answer_type=AnswerType.QUESTION_HANDOFF if self.is_handoff else AnswerType.QUESTION_SELFHANDLING)
