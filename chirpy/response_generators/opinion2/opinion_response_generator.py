from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_generator_datatypes import emptyResult
from chirpy.core.entity_linker.entity_groups import ENTITY_GROUPS_FOR_CLASSIFICATION
from chirpy.response_generators.opinion2.policies.two_turn_agree_policy import TwoTurnAgreePolicy
from chirpy.response_generators.opinion2.policies.disagree_agree_switch_agree_policy import DisagreeAgreeSwitchAgreePolicy
from chirpy.response_generators.opinion2.policies.short_soft_disagree_policy import ShortSoftDisagreePolicy
from chirpy.annotators.corenlp import Sentiment, CorenlpModule
import re
import random
import logging
from collections import defaultdict
import chirpy.response_generators.opinion2.utils as utils
import chirpy.response_generators.opinion2.state_actions as state_actions
import chirpy.response_generators.opinion2.opinion_sql as opinion_sql
from typing import List, Optional, Tuple
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name
from chirpy.response_generators.opinion2.constants import ACTION_SPACE
from chirpy.response_generators.opinion2.policies.baseline_policies import AlwaysAgreePolicy
from chirpy.response_generators.opinion2.policies.always_disagree_policy import AlwaysDisagreePolicy
from chirpy.response_generators.opinion2.policies.disagree_agree_policy import DisagreeAgreePolicy
from chirpy.response_generators.opinion2.policies.disagree_switch_agree_policy import DisagreeSwitchAgreePolicy
from chirpy.response_generators.opinion2.policies.soft_disagree_switch_agree_policy import SoftDisagreeSwitchAgreePolicy
from chirpy.core.response_generator_datatypes import PromptResult, ResponseGeneratorResult, UpdateEntity, emptyPrompt, emptyResult
from chirpy.response_generators.opinion2.state_actions import Action, AdditionalFeatures, State
from chirpy.response_generators.opinion2.utterancify import fancy_utterancify, fancy_utterancify_prompt
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator.neural_helpers import get_neural_fallback_handoff
from chirpy.core.util import DAYS_OF_WEEK, contains_phrase, get_eastern_dayofweek

from chirpy.core.response_generator.state import NO_UPDATE

NOS = r'[(no)\s]+(.*)'

MENTION_REMEMBER_TRANSITIONS = [
    "Oh hey, I just thought of something you said a little while back. ",
    "Changing the subject a little, there was something you mentioned that I wanted to chat about. ",
    "This is kind of random, but I was just thinking about what you said earlier. ",
     "Hey, if you'd be alright with changing the subject, you mentioned something before that I wanted to follow up on. ",
    "Umm, I hope you don't mind that this is sort of off topic, but I'm interested in something you brought up earlier. ",
     "So, changing the subject a little, I just thought of something I wanted to chat about. "
]

DO_YOU_LIKE_TRANSITIONS = [
    "Hey, so going off topic, I'm having fun getting to know you and I wanted to hear more of your opinions. ",
    "Anyways, um, there was actually something else I wanted to ask you. ",
    "Sorry to be going off topic, but I just remembered something I meant to ask you. ",
    "So, this is a bit random, but I thought of an unrelated question I had for you. ",
    "Hmm, on a different subject, there's something I've been curious about. ",
    "So, the best part of my job is getting to know new people and there's actually something kind of random I've been wanting to ask you. ",
]

logger = logging.getLogger('chirpylogger')

class OpinionResponseGenerator2(ResponseGenerator):
    name='OPINION'
    def __init__(self, state_manager) -> None:
        super().__init__(state_manager, state_constructor=State, conditional_state_constructor=State,
                         disallow_start_from=['PERSONAL ISSUES', 'SPORTS'])
        self.logger = logging.getLogger('chirpylogger')

    def init_state(self) -> State:
        return State()

    def initialize_turn(self):
        self.policies = {repr(policy): policy for policy in [AlwaysAgreePolicy(), AlwaysDisagreePolicy(),
             DisagreeAgreePolicy(), DisagreeSwitchAgreePolicy(), SoftDisagreeSwitchAgreePolicy(),
             ShortSoftDisagreePolicy(), DisagreeAgreeSwitchAgreePolicy(), TwoTurnAgreePolicy()]}
        self.policy_rates = [(repr(AlwaysAgreePolicy()), 0.4),
                             (repr(SoftDisagreeSwitchAgreePolicy()), 0.3),
                             (repr(DisagreeAgreeSwitchAgreePolicy()), 0.3)]
        self.short_policy_rates = [(repr(TwoTurnAgreePolicy()), 1.0)]
        self.agree_policies_rates = [(repr(AlwaysAgreePolicy()), 1.0)]
        self.disagree_policy_rates = [(repr(SoftDisagreeSwitchAgreePolicy()), 0.5),
                             (repr(DisagreeAgreeSwitchAgreePolicy()), 0.5)]
        self.opinionable_phrases = {phrase.text : phrase for phrase in opinion_sql.get_opinionable_phrases()}
        self.opinionable_entities = defaultdict(list)
        for phrase in self.opinionable_phrases.values():
            if phrase.wiki_entity_name is not None:
                self.opinionable_entities[phrase.wiki_entity_name].append(phrase)

    def respond_neg_nav(self, state : State, wiki_entity : Optional[WikiEntity]) -> ResponseGeneratorResult:
        """This method generates the result when user says "change the subject"

        :param state: the current state
        :type state: State
        :param wiki_entity: the current WIKI entity that we are using
        :type wiki_entity: Optional[WikiEntity]
        :return: a result that can be directly returned from the get_response function
        :rtype: ResponseGeneratorResult
        """

        self.logger.primary_info('NavigationalIntent is negative, so doing a hard switch out of OPINION') # type: ignore
        conditional_state = state.reset_state()
        conditional_state.last_turn_select = True
        return ResponseGeneratorResult(
            text=get_neural_fallback_handoff(self.state_manager.current_state) or "Ok, cool.",
            priority=ResponsePriority.WEAK_CONTINUE,
            needs_prompt=True,
            state=state,
            cur_entity=None,
            conditional_state=conditional_state)

    def populate_features(self, state : State, utterance : str) -> AdditionalFeatures:
        """This method populates the additional features that can be extracted through the pipeline. For now it populates

        1. A list of detected phrases (including phrases already talked about)
        2. Whether user said yes or no in this turn
        3. Whether user said like or dislike in this turn

        :param state: the current state
        :type state: State
        :param utterance: the current utterance
        :type utterance: str
        :param phrase2entity: the dictionary of phrase -> wiki_entity
        :type phrase2entity: Dict[str, str]
        :param entity2phrases: the reverse dictionary of wiki_entity -> phrase
        :type entity2phrases: Dict[str, List[str]]
        :return: an additional features object containing all the detected features
        :rtype: AdditionalFeatures
        """
        additional_features = AdditionalFeatures()

        # First get the detected phrases
        linked_spans = self.state_manager.current_state.entity_linker.all_linkedspans # type: ignore
        linked_wiki_entity_names = set(linked_span.top_ent.name for linked_span in linked_spans)
        detected_phrases = [phrase.text \
            for wiki_entity_name, phrases in self.opinionable_entities.items() if wiki_entity_name in linked_wiki_entity_names\
            for phrase in phrases]
        if len(detected_phrases) > 0:
            self.logger.primary_info(f'OPINION detected linked phrases {detected_phrases}') # type: ignore
        else:
            self.logger.primary_info(f'OPINION did not detect any linked phrases. Will check for non-linked phrases') # type: ignore
            utterance = self.state_manager.current_state.text
            detected_phrases = [phrase_text for phrase_text in self.opinionable_phrases if contains_phrase(utterance, set([phrase_text]))]
            if len(detected_phrases) > 0:
                self.logger.primary_info(f'OPINION detected nonlinked phrases {detected_phrases}') # type: ignore
        if self.get_navigational_intent_output().pos_intent:
            self.logger.primary_info("OPINION received positive navigational intent, so don't add to detected phrases")
            additional_features.current_posnav_phrases = tuple(detected_phrases)
            detected_phrases = []
        additional_features.detected_phrases = tuple([phrase for phrase in detected_phrases])

        reverse_questions = ["are you", "do you", "would you", "why do you", "why are you", "what do you", "when do you", "what do you", "what do"]
        if any(utterance.startswith(x) for x in reverse_questions):
            #print("Detected a reverse question, stopping.")
            return None

        # Then detect whether user said yes
        if self.state_manager.current_state.dialogact['is_yes_answer']: # type: ignore
            self.logger.primary_info(f'OPINION detected user said YES through dialog act') # type: ignore
            additional_features.detected_yes = True
        elif utils.is_high_prec_yes(utterance):
            self.logger.primary_info(f'OPINION detected user said YES through bag of words') # type: ignore
            additional_features.detected_yes = True
        else:
            additional_features.detected_yes = False
        if self.state_manager.current_state.dialogact['is_no_answer']: # type: ignore
            self.logger.primary_info(f'OPINION detected user said NO through dialog act') # type: ignore
            additional_features.detected_no = True
        elif utils.is_high_prec_no(utterance):
            self.logger.primary_info(f'OPINION detected user said NO through bag of words') # type: ignore
            additional_features.detected_no = True
        else:
            additional_features.detected_no = False

        # Then detect whether user said like or dislike
        sentiment = self.state_manager.current_state.corenlp['sentiment']  # type: ignore
        if len(utterance.split(' ')) > 0 and utterance.split(' ')[0] == 'no':
            no_stripped_matches = re.match(NOS, utterance)
            no_stripped_utterance = no_stripped_matches.groups()[0] if no_stripped_matches is not None else ''
            if len(no_stripped_utterance) > 0:
                self.logger.info(f'Opinion detected user saying no in the beginning, stripped it to {no_stripped_utterance} and rerun sentiment analysis')
                sentiment = Sentiment.NEUTRAL # First set sentiment to neutral
                corenlp_module = CorenlpModule(self.state_manager)
                msg = {'text': no_stripped_utterance, "annotators": ["sentiment"]}
                response = corenlp_module.execute(msg)
                if response is not None and 'sentiment' in response:
                    sentiment = response['sentiment']
        self.logger.primary_info(f'Opinion detected user opinion sentiment {sentiment}') # type: ignore


        like, like_reason = utils.is_like(utterance)
        if like or (sentiment.value > 2 and len([word for word in utterance.split(' ') if word not in ['yes', 'no']]) > 0):
            additional_features.detected_like = True
            additional_features.detected_user_gave_reason = like_reason is not None
        dislike, dislike_reason = utils.is_not_like(utterance)
        if dislike or (sentiment.value < 2 and len([word for word in utterance.split(' ') if word not in ['yes', 'no']]) > 0):
            additional_features.detected_dislike = True
            additional_features.detected_user_gave_reason = dislike_reason is not None
        if like and state.cur_sentiment < 2:
            additional_features.detected_user_sentiment_switch = True
        if dislike and state.cur_sentiment > 2:
            additional_features.detected_user_sentiment_switch = True

        if utils.is_high_prec_interest(utterance):
            additional_features.detected_user_disinterest = False
        elif utils.is_high_prec_disinterest(utterance):
            additional_features.detected_user_disinterest = True
        elif len(utterance.split(' ')) < 4 \
                and (not additional_features.detected_like and not additional_features.detected_dislike)\
                and not additional_features.detected_yes:
            additional_features.detected_user_disinterest = True
        self.logger.primary_info(f'OPINION populated additional features to be {additional_features}') # type: ignore
        return additional_features

    def get_action_space(self, state : State, pos_reasons : List[str], neg_reasons : List[str], related_entities : List[str]) -> List[Action]:
        """This method gets the potential action spaces. Essentially it removes impossible actions, such as giving a reason when there is no reason,
        or suggesting an alternative entity when there is none

        :param state: the current state
        :type state: State
        :param pos_reasons: a list of positive reasons
        :type pos_reasons: List[str]
        :param neg_reasons: a list of negative reasons
        :type neg_reasons: List[str]
        :param related_entities: a list of related entities
        :type related_entities: List[str]
        :return: a list of available actions for the policy to chose from
        :rtype: List[Action]
        """
        action_space = ACTION_SPACE
        user_sentiment_history = dict(state.user_sentiment_history)
        if state.cur_phrase in user_sentiment_history:
            self.logger.info(f'Opinion detected user already have an opinion on {state.cur_phrase}, will disallow opinion solicitation')
            action_space = filter(lambda action: not action.solicit_opinion, action_space)
        if len(pos_reasons) == 0:
            self.logger.info(f'Opinion detected no positive reasons, will disallow giving a positive reason')
            action_space = filter(lambda action: action.sentiment != 4 or not action.give_reason, action_space)
        if len(neg_reasons) == 0:
            self.logger.info(f'Opinion detected no negative reasons, will disallow giving a negative reason')
            action_space = filter(lambda action: action.sentiment != 0 or not action.give_reason, action_space)
        if len(related_entities) == 0:
            self.logger.info(f'Opinion detected no related entities, will disallow suggesting an alternative')
            action_space = filter(lambda action: not action.suggest_alternative, action_space)
        action_space = list(action_space)
        return action_space

    def continue_conversation(self, response_types) -> Optional[ResponseGeneratorResult]:
        # TODO get rid of this if OPINION is *ever* refactored
        return None

    def handle_rejection_response(self, *args, **kwargs):
        logger.primary_info("OPINION is calling handle_rejection_response")
        state, utterance, _ = self.get_state_utterance_response_types()
        ok_negnavs = ['don\'t like', 'hate', 'do not like', 'dislike']
        if state.action_history[-1].solicit_opinion and any(o in utterance for o in ok_negnavs):
            logger.primary_info("OPINION disabling rejection_response handler because we solicited an opinion on the last turn.")
            return None
        return super().handle_rejection_response(*args, **kwargs)

    def handle_default_post_checks(self) -> Optional[ResponseGeneratorResult]:
        """This function defines the stages that we go through to generate the result. The procedure is

        1. First populate the "additional_features"
        2. Incorporate unconditional information such as user's likes and dislikes, phrases that were detected
        3. Advance the state to the next state depending on the user's utterance and additional features
        4. Define the action space for the policy
        5. Select an action using a policy
        6. Utterancify the action chosen using additional information like lists of reasons and alternatives
        7. Post process the state conditioned on the action
        8. Construct Cobot specific classes such as ResponseGeneratorResult

        :param state: the current state
        :type state: State
        :return: a result that can be used for cobot
        :rtype: ResponseGeneratorResult
        """
        state = self.state
        utterance = self.state_manager.current_state.text
        self.initialize_turn()
        neg_intent = self.state_manager.current_state.navigational_intent.neg_intent  # type: ignore

        # if neg_intent and self.state_manager.last_state_active_rg == 'OPINION': # type: ignore
        #     ok_negnavs = ['don\'t like', 'hate', 'do not like', 'dislike']
        #     if not state.action_history[-1].solicit_opinion and any(o in utterance for o in ok_negnavs):
        #         logger.primary_info("OPINION found negative intent, so doing a hard exit!")
        #         return self.respond_neg_nav(state, None)
        #     else:
        #         logger.primary_info("OPINION found that negative intent should be handled by RG as an opinion")

        additional_features = self.populate_features(state, utterance)
        if additional_features is None:
            return self.emptyResult()
        high_prec = self.state_manager.current_state.entity_linker.high_prec # type: ignore
        # should_evaluate = len(state.action_history) > 4 and not state.evaluated \
        #     and not state.first_episode and state.cur_policy != '' and state.cur_policy != repr(OneTurnAgreePolicy())

        should_evaluate = False # Turning off evaluation question.


        # This should no longer be necessary because we have posnav handling. -- Ethan
        # PS this may break some tests
        # if self.state_manager.current_state.entity_linker.high_prec and state.cur_phrase != '': # type: ignore
        #     import pdb; pdb.set_trace()
        #     cur_entity_name = self.opinionable_phrases[state.cur_phrase].wiki_entity_name
        #     if (cur_entity_name is None and state.cur_phrase not in [linked_span.span for linked_span in high_prec]) \
        #             or (cur_entity_name is not None and cur_entity_name not in [linked_span.top_ent.name for linked_span in high_prec]):
        #         # If the above condition passes, it means that the linked entity is not the currently opinionating phrase.
        #         if len(additional_features.detected_phrases) == 0:
        #             # User no longer want to talk about an opinionable phrase
        #             return self.respond_neg_nav(state, random.choice(self.state_manager.current_state.entity_linker.high_prec).top_ent) # type: ignore

        if state.last_turn_prompt or state.last_turn_select:
            priority = ResponsePriority.STRONG_CONTINUE
        elif len(high_prec) > 0 and \
                not any(linked_span.span in self.opinionable_phrases \
                        or linked_span.top_ent.name in self.opinionable_entities for linked_span in high_prec): # type: ignore
            self.logger.primary_info(f'Opinion realized that there is a high precision entity, will not CAN_START our conversation') # type: ignore
            priority = ResponsePriority.NO
        # if WhatsYourOpinion().execute(utterance) is not None:
        #     self.logger.primary_info(f"Opinion detected user is asking for our opinion, raising priority to FORCE_START") # type: ignore
        #     priority = ResponsePriority.FORCE_START
        else:
            priority = self._get_priority_from_answer_type()
        if len(state.action_history) > 0 and state.action_history[-1].exit:
            self.logger.primary_info(f'Opinion detected our previous action is to exit and we were not selected, will reset the state before this turn starts') # type: ignore
            state = state.reset_state()
            priority = ResponsePriority.CAN_START # Drop the priority to CAN_START because we already ended a convo before
        # First need to incorporate the unconditional information learned from this turn
        state.detected_opinionated_phrases += additional_features.detected_phrases
        state.detected_opinionated_phrases = list(set(state.detected_opinionated_phrases))
        if len(additional_features.detected_phrases) > 0:
            # Here we only use regex since sentiment analysis may not always do well
            if utils.is_like(utterance)[0] or self.get_last_active_rg() == 'CATEGORIES':
                state.user_sentiment_history += tuple((phrase, 4) for phrase in additional_features.detected_phrases)
            elif utils.is_not_like(utterance)[0]:
                state.user_sentiment_history += tuple((phrase, 0) for phrase in additional_features.detected_phrases)
        additional_features.detected_phrases = tuple([phrase for phrase in additional_features.detected_phrases if phrase not in state.phrases_done])

        # Then need to advance the state using the utterance
        entity_tracker = self.get_entity_tracker()
        state_p = state_actions.next_state(state, utterance, additional_features, entity_tracker)
        if state_p is None or state_p.cur_phrase is None:
            return emptyResult(state.reset_state())
        reasons_used = dict(state.reasons_used)
        phrase_reasons_used = set(reasons_used[state_p.cur_phrase]) if state_p.cur_phrase in reasons_used else []
        # logger.primary_info(f"Cur phrase: {state_p.cur_phrase}")
        pos_reasons, neg_reasons = utils.get_reasons(state_p.cur_phrase)
        pos_reasons = [reason for reason in pos_reasons if reason not in phrase_reasons_used]
        neg_reasons = [reason for reason in neg_reasons if reason not in phrase_reasons_used]
        # logger.primary_info(f"pos_reasons: {pos_reasons}")
        # logger.primary_info(f"neg_reasons: {neg_reasons}")
        related_entities = [phrase.text for phrase in self.opinionable_phrases.values() \
            if phrase.category is not None and phrase.category == self.opinionable_phrases[state_p.cur_phrase].category \
                and phrase.wiki_entity_name != self.opinionable_phrases[state_p.cur_phrase].wiki_entity_name]
        related_entities = [e for e in related_entities if e not in state_p.phrases_done]

        # Then need to define the action space
        action_space = self.get_action_space(state_p, pos_reasons, neg_reasons, related_entities)
        # Then need to select a policy if we don't have one
        ab_test_policy = self.state_manager.current_state.experiments.look_up_experiment_value('opinion_policy') # type: ignore
        if state_p.cur_policy != '':
            self.logger.primary_info(f'OPINION is using current policy {state_p.cur_policy} to respond to the user') # type: ignore
        elif ab_test_policy != 'random' or ab_test_policy == 'not_defined':
            state_p.cur_policy = ab_test_policy
            self.logger.primary_info(f'Opinion detected a/b test policy is {ab_test_policy}, will set current episode accordingly ') # type: ignore
        # Ethan: disabling because OPINION is now lower priority.
        # elif state_p.num_turns_since_long_policy < 20:
        #     policies, weights = zip(*self.short_policy_rates)
        #     state_p.cur_policy = random.choices(policies, weights, k=1)[0] # type: ignore
        #     self.logger.primary_info(f'Opinion had a long conversation {state_p.num_turns_since_long_policy} < 20 turns ago. Will use policy {state_p.cur_policy}') # type: ignore
        else:
            if state_p.last_policy in set([p for p, _ in self.disagree_policy_rates]):
                policies, weights = zip(*self.agree_policies_rates)
            elif state_p.last_policy in set([p for p, _ in self.agree_policies_rates]):
                policies, weights = zip(*self.agree_policies_rates)
            else:
                policies, weights = zip(*self.policy_rates)
            state_p.cur_policy = random.choices(policies, weights, k=1)[0] # type: ignore
            self.logger.primary_info(f'OPINION have no current policy, randomly picked {state_p.cur_policy} to respond to the user, resetting turn count') # type: ignore
        state_p.last_policy = state_p.cur_policy
        policy = self.policies[state_p.cur_policy] # type: ignore
        # Then need to get the action from a policy
        action = policy.get_action(state_p, action_space, additional_features)
        self.logger.primary_info(f'OPINION\'s strategy chose action {action}') # type: ignore
        action_space = self.get_action_space(state_p, pos_reasons, neg_reasons, related_entities) # Redefine action space for checks in case cur_phrase changed
        if action not in action_space:
            self.logger.error(f'OPINION policy {repr(policy)} generated an action {action} that is not in the action space {action_space}. Check policy implementation.')
            new_state = state.reset_state()
            return emptyResult(new_state)
        # Then need to utterancify the action
        text, phrase, reason = fancy_utterancify(state_p, action, pos_reasons, neg_reasons,
                                                related_entities, should_evaluate, self.choose, additional_features=additional_features) # type: ignore
        if self.get_navigational_intent_output().pos_intent:
            text = "Sure, happy to! " + text
        # Then need to fill the rest of the fields of state_p (through mutation)
        state_p = state_actions.fill_state_on_action(state_p, action, text, phrase, additional_features, reason,
            self.opinionable_phrases, self.opinionable_entities)

        # Then need to fill the rest of the cobot specific fields
        state_p.last_turn_select = True
        state_p.last_turn_prompt = False
        user_sentiment_history_dict = dict(state.user_sentiment_history)
        wiki_entity = None
        if phrase != '' and phrase in user_sentiment_history_dict and user_sentiment_history_dict[phrase] > 2 \
                and self.opinionable_phrases[phrase].good_for_wiki:
            wiki_entity = get_entity_by_wiki_name(self.opinionable_phrases[phrase].wiki_entity_name)
        state.last_turn_prompt, state.last_turn_select = False, False
        needs_prompt = False
        if action.exit:
            if len(state_p.action_history) > 6:
                self.logger.primary_info(f"Opinion had a conversation of length {len(state_p.action_history)}, will reset long_policy count") # type: ignore
                state_p.num_turns_since_long_policy = 0
            if not should_evaluate:
                needs_prompt = True
            if len(state_p.action_history) < 4:
                self.logger.primary_info(f"Opinion only had 4 turns. Will WEAK_CONTINUE the conversation") # type: ignore
                priority = ResponsePriority.WEAK_CONTINUE
            state_p.first_episode = False
        return ResponseGeneratorResult(text, priority, needs_prompt, state, wiki_entity, conditional_state=state_p)

    def select_phrase_for_prompt(self, state : State) -> Tuple[Optional[str], PromptType, str]:
        """This method selects a phrase for us to prompt. Logically

        1. First checks if the current tracked entity is something we can opinionate about
        2. Then checks if user said any recent phrases that we can use
        3. Then checks if user said any phrase at all that we can use
        4. Then checks if we have a generic entity that are still available for user to use

        :param state: the current state
        :type state: State
        :return: a phrase and a priority for that phrase
        :rtype: Tuple[Optional[str], PromptType]
        """
        phrases_done = set(state.phrases_done)
        generic_available_phrases = [phrase for phrase in self.opinionable_phrases.values() \
                if phrase.text not in phrases_done and phrase.generic \
                and (phrase.wiki_entity_name not in DAYS_OF_WEEK or phrase.wiki_entity_name == get_eastern_dayofweek())]
        if hasattr(self.state_manager.current_state, 'entity_tracker'):
            cur_entity = self.get_current_entity(initiated_this_turn=False) # type:ignore
            # If the current entity is what we are talking
            if cur_entity is not None and cur_entity.name in self.opinionable_entities \
                    and any(phrase.text not in state.phrases_done for phrase in self.opinionable_entities[cur_entity.name]):
                phrase = random.choice([phrase.text for phrase in self.opinionable_entities[cur_entity.name] if phrase.text not in state.phrases_done])
                priority = PromptType.CURRENT_TOPIC
                self.logger.primary_info(f'OPINION is prompting with tracked entity {cur_entity} with phrase {phrase}') # type: ignore
                return phrase, priority, ''
            # If we have a generic phrase of the same type as cur_entity
            if cur_entity is not None:
                for ent_group_name, ent_group in ENTITY_GROUPS_FOR_CLASSIFICATION.ordered_items:
                    if ent_group.matches(cur_entity):
                        phrases_of_ent_group = [phrase.text for phrase in generic_available_phrases if phrase.wiki_category == ent_group_name]
                        if len(phrases_of_ent_group) > 0:
                            phrase, priority = random.choice(phrases_of_ent_group), PromptType.CONTEXTUAL
                            self.logger.primary_info(f'Opinion is prompting {phrase} as contextual due to its entity group {ent_group_name} matching current entity\'s group') # type: ignore
                            return phrase, priority, f"Speaking of another {ent_group_name.replace('_', ' ')}, "
        recent_available_phrases = [phrase for phrase in state.detected_opinionated_phrases[-3:] \
                if phrase not in phrases_done]
        if len(recent_available_phrases) > 0:
            phrase = recent_available_phrases[-1]
            priority = PromptType.CONTEXTUAL
            self.logger.primary_info(f'Opinion is prompting a phrase user uttered before {phrase}') # type: ignore
            return phrase, priority, self.choose(MENTION_REMEMBER_TRANSITIONS) # type: ignore
        uttered_available_phrases = [phrase for phrase in state.detected_opinionated_phrases \
                if phrase not in phrases_done]
        if len(uttered_available_phrases) > 0:
            phrase = random.choice(uttered_available_phrases)
            priority = PromptType.CONTEXTUAL
            self.logger.primary_info(f'Opinion cannot find a recent phrase, prompting a phrase from user utterance history {phrase}') # type: ignore
            return phrase, priority, self.choose(MENTION_REMEMBER_TRANSITIONS) # type: ignore
        if len(generic_available_phrases) > 0:
            phrase = random.choice(generic_available_phrases).text
            priority = PromptType.GENERIC
            self.logger.primary_info(f'Opinion cannot find a recent phrase or an uttered phrase, prompting a generic phrase {phrase}') # type: ignore
            return phrase, priority, self.choose(DO_YOU_LIKE_TRANSITIONS) # type: ignore
        return None, PromptType.GENERIC, ''

    def get_prompt(self, state: State) -> PromptResult:
        """This method is the same as get_response. Only difference is that

        1. we do not get a list of reasons (because there is not enough time)
        2. we only chose to solicit an opinion if user didn't have an opinion on it before, or
        3. we will solicit a reason if user told us before that they like or dislike a phrase

        :param state: the current state
        :type state: State
        :return: a result cobot can use
        :rtype: PromptResult
        """
        logger.info(f"{self.name} is running get_prompt()")
        self.state = state
        self.response_types = self.get_cache(f'{self.name}_response_types')
        self.initialize_turn()
        if state.last_turn_prompt:
            return self.emptyPrompt()
        phrase, priority, transition_phrase = self.select_phrase_for_prompt(state)
        if phrase is None:
            return self.emptyPrompt()
        utterance = self.state_manager.current_state.text
        additional_features = self.populate_features(state, utterance)
        if additional_features is None:
            return self.emptyPrompt()
        additional_features.detected_phrases = tuple([phrase for phrase in additional_features.detected_phrases if phrase not in state.phrases_done])

        # Then need to advance the state using the utterance
        entity_tracker = self.get_entity_tracker()
        state_p = state_actions.next_state(state, utterance, additional_features, entity_tracker)
        if state_p is None:
            # Special handling for prompt: Add phrase and sentiment
            state_p = state.reset_state()
            state_p.cur_phrase = phrase
            user_sentiments_history = dict(state_p.user_sentiment_history)
            state_p.cur_sentiment = user_sentiments_history[phrase] if phrase in user_sentiments_history else 2
        if state_p.cur_sentiment != 2:
            action = Action(solicit_reason=True)
        else:
            action = Action(solicit_opinion=True)
        # Then need to utterancify the action
        text, phrase, reason = fancy_utterancify_prompt(state_p, action, [], [], [], state_p.cur_phrase not in state.detected_opinionated_phrases,
                                                        self.choose) # type: ignore
        # Then need to fill the rest of the fields of state_p (through mutation)
        state_p = state_actions.fill_state_on_action(state_p, action, text, phrase, additional_features, reason,
            self.opinionable_phrases, self.opinionable_entities)

        # Then need to fill the rest of the cobot specific information
        state_p.last_turn_prompt, state_p.last_turn_select = True, False
        wiki_entity = None
        if self.opinionable_phrases[phrase].good_for_wiki:
            wiki_entity = get_entity_by_wiki_name(self.opinionable_phrases[phrase].wiki_entity_name)
        state.last_turn_prompt, state.last_turn_select = False, False

        text = ' '.join((transition_phrase, text))

        return PromptResult(text, priority, state, wiki_entity, conditional_state=state_p)

    def update_state_if_chosen(self, state: State, conditional_state : Optional[State]) -> State:
        if conditional_state is not None and conditional_state.num_turns_since_long_policy != NO_UPDATE:
            conditional_state.num_turns_since_long_policy += 1
        for attr in dir(conditional_state):
            if not callable(getattr(conditional_state, attr)) and not attr.startswith("__"):
                val = getattr(conditional_state, attr)
                if val != NO_UPDATE: setattr(state, attr, val)
        return state

    def update_state_if_not_chosen(self, state: State, conditional_state : Optional[State]) -> State:
        new_state = state.reset_state()
        new_state.num_turns_since_long_policy += 1
        return new_state
