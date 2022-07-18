from enum import IntEnum
import logging

from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.smooth_handoffs import SmoothHandoff
from typing import Optional
from chirpy.core.entity_linker.entity_groups import EntityGroup


logger = logging.getLogger('chirpylogger')


class AnswerType(IntEnum):
    NONE = 1
    QUESTION_SELFHANDLING = 2
    QUESTION_HANDOFF = 3
    STATEMENT = 4
    ENDING = 5


CONTINUING_ANSWER_TYPES = [AnswerType.QUESTION_SELFHANDLING, AnswerType.QUESTION_HANDOFF, AnswerType.STATEMENT]

class ResponseGeneratorResult:
    def __init__(self,
                 text: Optional[str],
                 priority: ResponsePriority,
                 needs_prompt: bool,
                 state,
                 cur_entity: Optional[WikiEntity],
                 answer_type: AnswerType = AnswerType.NONE,
                 expected_type: Optional[EntityGroup] = None,
                 smooth_handoff: Optional[SmoothHandoff] = None,
                 conditional_state=None,
                 tiebreak_priority=None,
                 no_transition=False,
                 last_rg_willing_to_handover_control=False,  # EDIT
                 rg_that_was_taken_over =None,  # EDIT
                 takeover_rg_willing_to_handback_control=False  # EDIT
                 ):
        """
        :param text: text of the response
        :param priority: priority of the response
        :param needs_prompt: whether the response needs a prompt from another response generator
        :param state: response generator state to be persisted between turns
        :param conditional_state: information that will be passed to the RG's update_if_chosen or update_if_not_chosen
            function (depending on whether the response is chosen), to be used by the RG to update its state accordingly.
        :param expected_type: If provided, an EntityGroup representing the types of entities the user might mention on
            the next turn. Providing an expected_type makes it easier for entities of that type to become cur_entity
            on the next turn.
        :param smooth_handoff: If provided, is an identifier to signal that we want a particular "smooth handoff" to
            happen, i.e. some other RG(s) should give a particular prompt with FORCE_START. If this response is chosen,
            current_state.smooth_handoff will be set to this value. Should only be provided if needs_prompt=True.
        :param cur_entity: a WikiEntity defining what the new topic of conversation is if this response is chosen.
            If None, this means that we have no current topic, or the current topic cannot be defined by a single
            entity (this is the case in LAUNCH, for example)
        """
        self.text = text
        if text:
            self.text = text.strip()
        else:
            if priority != ResponsePriority.NO:
                logger.error('Trying to create a ResponseGeneratorResult with text={} and priority={}. '
                             'Priority should be NO if text is None or empty. Changing the priority to NO.'.format(
                                text, priority.name), stack_info=True)
                priority = ResponsePriority.NO
        if not isinstance(priority, ResponsePriority):
            raise TypeError(f'Trying to create a ResponseGeneratorResult with priority={priority}, which is of '
                            f'type {type(priority)}. It should be type {ResponsePriority}')
        self.priority = priority
        self.needs_prompt = needs_prompt
        if cur_entity is not None and not isinstance(cur_entity, WikiEntity):
            raise TypeError(f'Trying to create a ResponseGeneratorResult with cur_entity={cur_entity}, which is of '
                             f'type {type(cur_entity)}. It should be None or type {WikiEntity}')
        self.cur_entity = cur_entity
        self.answer_type = answer_type
        if not isinstance(answer_type, AnswerType):
            raise TypeError(f'Trying to create a ResponseGeneratorResult with answer_type={answer_type}, which is of type'
                            f'{type(answer_type)} and not AnswerType.')
        if needs_prompt:
            logger.primary_info("Setting AnswerType to AnswerType.ENDING because needs_prompt=True.")
            self.answer_type = AnswerType.ENDING
        if expected_type is not None and not isinstance(expected_type, EntityGroup):
            raise TypeError(f'Trying to create a ResponseGeneratorResult with expected_type={expected_type}, which is '
                             f'of type {type(expected_type)}. It should be None or a EntityGroup')
        if expected_type and needs_prompt:
            raise ValueError(f"Trying to create a ResponseGeneratorResult with expected_type={expected_type} and "
                             f"needs_prompt={needs_prompt}. A response should not have an expected_type if "
                             f"needs_prompt=True because the prompting RG determines the expected_type (if any).")

        self.expected_type = expected_type
        if smooth_handoff is not None and not isinstance(smooth_handoff, SmoothHandoff):
            raise TypeError(f'Trying to create a ResponseGeneratorResult with smooth_handoff={smooth_handoff}, which is '
                            f'of type {type(smooth_handoff)}. It should be None or an instance of {SmoothHandoff}')

        if smooth_handoff is not None and not needs_prompt:
            raise ValueError(f"Trying to create a ResponseGeneratorResult with smooth_handoff={smooth_handoff} and "
                             f"needs_prompt={needs_prompt}. A response should not have a smooth_handoff if "
                             f"needs_prompt=False.")
        self.smooth_handoff = smooth_handoff
        self.state = state
        self.conditional_state = conditional_state
        self.tiebreak_priority = tiebreak_priority
        self.no_transition = no_transition
        self.last_rg_willing_to_handover_control = last_rg_willing_to_handover_control  # EDIT
        self.rg_that_was_taken_over  = rg_that_was_taken_over     # EDIT
        self.takeover_rg_willing_to_handback_control = takeover_rg_willing_to_handback_control # EDIT

    def reduce_size(self, max_size:int = None):
        """Gracefully degrade by removing non essential attributes.
        This function is called if the size is too large and the object needs to be purged

        max_size - this parameter is ignored"""
        attributes = ['state', 'conditional_state']
        for attribute in attributes:
            try:
                delattr(self, attribute)
            except AttributeError as e:
                logger.warning(f"{self} has no attribute {attribute} for purging")


    def __repr__(self):
        return 'ResponseGeneratorResult(' + ', '.join(f'{key}={value}' for key, value in self.__dict__.items()) + ')'


class PromptResult:
    def __init__(self,
                 text: Optional[str],
                 prompt_type: PromptType,
                 state,
                 cur_entity: Optional[WikiEntity],
                 expected_type: Optional[EntityGroup] = None,
                 conditional_state=None,
                 answer_type: AnswerType = AnswerType.QUESTION_SELFHANDLING,
                 last_rg_willing_to_handover_control=False,  # EDIT
                 rg_that_was_taken_over =None,  # EDIT
                 takeover_rg_willing_to_handback_control=False,  # EDIT
                 resuming_conversation_next_treelet=None   # EDIT
                 ):
        """
        :param text: text of the response
        :param prompt_type: the type of response being given, typically CONTEXTUAL or GENERIC
        :param state: response generator state to be kept between turns (regardless of whether the prompt is chosen)
        :param conditional_state: information that will be passed to the RG's update_if_chosen or update_if_not_chosen
            function (depending on whether the response is chosen), to be used by the RG to update its state accordingly.
        :param expected_type: If provided, an EntityGroup representing the types of entities the user might mention on
            the next turn. Providing an expected_type makes it easier for entities of that type to become cur_entity
            on the next turn.
        :param cur_entity: a WikiEntity defining what the new topic of conversation is if this prompt is chosen.
            If None, this means that we have no current topic, or the current topic cannot be defined by a single
            entity (this is the case in LAUNCH, for example)
        """

        self.text = text
        if text:
            self.text = text.strip()
        else:
            if prompt_type != PromptType.NO:
                logger.error('Trying to create a PromptResult with text={} and type={}. '
                             'Type should be NO if text is None or empty. Changing the type to NO.'.format(
                    text, prompt_type.name), stack_info=True)
                prompt_type = PromptType.NO
        if not isinstance(prompt_type, PromptType):
            raise TypeError(f'Trying to create a PromptResult with prompt_type={prompt_type}, which is of '
                            f'type {type(prompt_type)}. It should be type {PromptType}')
        self.type = prompt_type
        if cur_entity is not None and not isinstance(cur_entity, WikiEntity):
            raise TypeError(f'Trying to create a PromptResult with cur_entity={cur_entity}, which is of '
                             f'type {type(cur_entity)}. It should be None or type {WikiEntity}')
        self.cur_entity = cur_entity
        if expected_type is not None and not isinstance(expected_type, EntityGroup):
            raise TypeError(f'Trying to create a PromptResult with expected_type={expected_type}, which is '
                             f'of type {type(expected_type)}. It should be None or EntityGroup')
        self.expected_type = expected_type
        self.state = state
        self.conditional_state = conditional_state
        self.answer_type = answer_type
        self.last_rg_willing_to_handover_control = last_rg_willing_to_handover_control  # EDIT
        self.rg_that_was_taken_over  = rg_that_was_taken_over   # EDIT
        self.takeover_rg_willing_to_handback_control = takeover_rg_willing_to_handback_control  # EDIT
        self.resuming_conversation_next_treelet = resuming_conversation_next_treelet  # EDIT

    def __repr__(self):
        return 'PromptResult' + str(self.__dict__)

    def reduce_size(self, max_size: int=None):
        """Gracefully degrade by removing non essential attributes.
        This function is called if the size is too large and the object needs to be purged

        max_size - this parameter is ignored"""
        attributes = ['state', 'conditional_state']
        for attribute in attributes:
            try:
                delattr(self, attribute)
            except AttributeError as e:
                logger.warning(f"{self} has no attribute {attribute} for purging")


class UpdateEntity:
    """
    This class represents the output of a RG's get_entity() function, which allows it to override the decision of the
    entity tracker on a particular turn.

    At the beginning of each turn, the last active RG (the RG that last spoke on the previous turn) runs its
    get_entity() function and returns an UpdateEntity object.

        If self.update is False, nothing happens - the entity tracker will set cur_entity using the usual rules.
        If self.update is True, the entity tracker will set self.cur_entity as the current entity (it will not use
            its usual rules).
    """
    def __init__(self, update: bool = False, cur_entity: Optional[WikiEntity] = None):
        self.update = update
        if update:
            self.cur_entity = cur_entity

    def __repr__(self):
        if self.update:
            return f"<UpdateEntity: update={self.update}, cur_entity={self.cur_entity}>"
        else:
            return f"<UpdateEntity: update={self.update}>"

def emptyResult(state):
    """Makes a ResponseGeneratorResult that has no text, priority NO, needs no prompt, and preserves the given state"""
    return ResponseGeneratorResult(text=None, priority=ResponsePriority.NO, needs_prompt=False, state=state,
                                   cur_entity=None)

def emptyResult_with_conditional_state(state, conditional_state):
    """Makes a ResponseGeneratorResult that has no text, priority NO, needs no prompt, but also takes a conditional_state"""
    return ResponseGeneratorResult(text=None, priority=ResponsePriority.NO, needs_prompt=False, state=state,
                                   cur_entity=None, conditional_state=conditional_state)

def emptyPrompt(state):
    """Makes a PromptResult that has no text and preserves the given state"""
    return PromptResult(text=None, prompt_type=PromptType.NO, state=state, cur_entity=None)

def emptyPrompt_with_conditional_state(state, conditional_state):
    """Makes a PromptResult that has no text, but also takes a conditional state"""
    return PromptResult(text=None, prompt_type=PromptType.NO, state=state, cur_entity=None, conditional_state=conditional_state)

KILLED_RESULT = ResponseGeneratorResult(text="Killed", priority=ResponsePriority.NO, needs_prompt=False, state=None, cur_entity=None)

def is_killed(result):
    return result.text == 'Killed'
