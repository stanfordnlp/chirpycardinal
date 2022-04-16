import logging
import random
import textstat

from chirpy.core.response_generator import ResponseGenerator
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.response_generator.response_type import ResponseType
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, AnswerType
from chirpy.response_generators.transition.failed_transition_to_entities import BANNED_TRANSITIONS
from chirpy.response_generators.transition.state import State, ConditionalState
from chirpy.response_generators.transition.transition_helpers import get_transitions, get_random_starter_text
from chirpy.response_generators.transition.state import NO_UPDATE

logger = logging.getLogger('chirpylogger')

FLESCH_KINCAID_THRESHOLD = 40.0

class TransitionResponseGenerator(ResponseGenerator):
    name='TRANSITION'

    def __init__(self, state_manager):
        super().__init__(state_manager, can_give_prompts=True,
                         state_constructor=State,
                         conditional_state_constructor=ConditionalState)

    def handle_custom_continuation_checks(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if ResponseType.NO in response_types:
            return ResponseGeneratorResult(text="OK, no worries. Let's move onto something else.",
                                           priority=ResponsePriority.STRONG_CONTINUE, needs_prompt=True,
                                           state=state, cur_entity=None)
        else:
            return self.emptyResult()

    def get_entity_to_transition_from(self):
        cur_ent = self.get_current_entity()
        is_it_current = True
        if not cur_ent:
            ent_cand = self.get_entities()['talked_finished']
            if len(ent_cand) == 0:  #unlikely it will happen
                ent_cand = self.get_entities()['user_mentioned_untalked']
                if len(ent_cand) == 0:
                    logger.primary_info("Didn't find any entity to transition FROM")
                    return None, None
            cur_ent = random.choice(ent_cand)
            is_it_current = False
        return cur_ent, is_it_current

    def get_entity_to_transition_to(self, from_entity):
        logger.primary_info(f"Getting related entities to transition from {from_entity.name}")
        transitions = get_transitions(from_entity.name)

        filtered_transitions = dict()
        for et, (ent, sent) in transitions.items():
            if ent.name in self.state.entities_prompted: continue
            if ent.name in BANNED_TRANSITIONS: continue
            if len(ent.name.split()) == 1 and ent.name.lower() not in sent: continue # single-word entities must appear in transition text
            if textstat.flesch_reading_ease(sent) <= FLESCH_KINCAID_THRESHOLD: continue # avoid difficult transitions
            if any([s.count(',') >= 4 for s in self.get_sentence_segments(sent)]): continue
            filtered_transitions[et] = (ent, sent)
        if len(filtered_transitions) == 0:
            logger.primary_info("Didn't find any entity to transition TO")
            return None
        transitions = list(filtered_transitions.items())
        return random.choices(transitions, weights=[x[0].pageview for _,x in transitions])[0]

    def get_current_transitional_entity(self):
        entity_tracker = self.get_entity_tracker()
        return entity_tracker.transitional_entity

    def handle_misc_prompt_checks(self):
        turns_since_last_active = self.get_current_state().turns_since_last_active

        # don't activate transition until after 10 user-bot turns
        if len(self.get_conversation_history()) // 2 < 10:
            return self.emptyPrompt()

        if len(self.get_conversation_history()) // 2 < 50:
            if not (turns_since_last_active['TRANSITION'] >= 15 and turns_since_last_active['WIKI'] >= 8):
                return self.emptyPrompt()
        else: # decrease intervals between transition prompts once the conversation is long
            if not (turns_since_last_active['TRANSITION'] >= 8 and turns_since_last_active['WIKI'] >= 4):
                return self.emptyPrompt()

        from_entity, is_it_current = self.get_current_transitional_entity(), True
        logger.primary_info(f"Detected current transitional entity: {from_entity}")
        
        if from_entity is None:    # no transitional entity, find something else
            from_entity, is_it_current = self.get_entity_to_transition_from()

        if not from_entity or from_entity.name in self.state.entities_prompted:
            logger.primary_info("Transition not activated because from_entity is either None or was \
                introduced by the RG itself")
            return self.emptyPrompt()

        transition_result = self.get_entity_to_transition_to(from_entity)
        if not transition_result:
            return self.emptyPrompt()

        logger.primary_info(f"Got the following entity to transition TO: {transition_result}")
        transition_entity, transition_text = transition_result[1][0], transition_result[1][1]

        starter_text = get_random_starter_text()
        question = f" do you wanna talk about {transition_entity.talkable_name}?"

        if not is_it_current:
            starter_text = f"I remember you mentioned {from_entity.talkable_name} earlier. " + starter_text
            prompt_type = PromptType.CONTEXTUAL
        else:
            starter_text = f"Speaking of {from_entity.talkable_name}, " + starter_text
            prompt_type = PromptType.CURRENT_TOPIC

        logger.primary_info("Chose to produce a transition.")
        return PromptResult(text=starter_text + transition_text + question,
                            prompt_type=prompt_type, state=self.state,
                            cur_entity=transition_entity,
                            conditional_state=ConditionalState(
                                entities_prompted=self.state.entities_prompted | {transition_entity.name},
                                from_entity=from_entity),
                            answer_type=AnswerType.STATEMENT,
                            )

    def update_state_if_chosen(self, state, conditional_state):
        
        if conditional_state:
            from_entity = conditional_state.from_entity
            entity_tracker = self.get_entity_tracker()
            if from_entity in entity_tracker.user_mentioned_untalked:
                logger.primary_info(f'Moving {from_entity} from {entity_tracker.user_mentioned_untalked} to {entity_tracker.talked_finished}')
                entity_tracker.user_mentioned_untalked = [e for e in entity_tracker.user_mentioned_untalked if e != from_entity]

            if from_entity != NO_UPDATE:
                entity_tracker.finish_entity(from_entity, transition_is_possible=False)

        return super().update_state_if_chosen(state, conditional_state)