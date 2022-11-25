from chirpy.core.callables import NamedCallable
from chirpy.core.state_manager import StateManager
from chirpy.core.regex import response_lists
from chirpy.core.response_generator.response_type import *
from chirpy.core.response_generator.neural_helpers import is_two_part, NEURAL_DECODE_CONFIG, get_random_fallback_neural_response
from chirpy.core.response_generator.state import NO_UPDATE, BaseSymbolicState, BaseSymbolicConditionalState
from chirpy.core.response_generator.neural_helpers import get_neural_fallback_handoff, neural_response_filtering
from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, emptyResult, \
    emptyResult_with_conditional_state, emptyPrompt, UpdateEntity, AnswerType
from chirpy.core.response_generator.helpers import *
from chirpy.core.response_generator.response_generator import ResponseGenerator
from chirpy.core.response_generator.supernode import Supernode, Subnode
from chirpy.core.response_priority import ResponsePriority
from chirpy.symbolic_rgs import global_nlu
from chirpy.core.util import load_text_file
from typing import Set, Optional, List, Dict
import logging
import os

from importlib import import_module

from concurrent import futures

logger = logging.getLogger('chirpylogger')

import os
STOPWORDS_FILEPATH = os.path.join(os.path.dirname(__file__), '../../data/long_stopwords.txt')
STOPWORDS = load_text_file(STOPWORDS_FILEPATH)


class SymbolicResponseGenerator(ResponseGenerator):
    name='SYMBOLIC_RESPONSE'
    def __init__(self,
                 state_manager,
                 supernodes=[
                    'FOOD__intro',
                    'GLOBALS'
                 ],
                 ):

        super().__init__(state_manager,  
            can_give_prompts=True,
            state_constructor=BaseSymbolicState,
            conditional_state_constructor=BaseSymbolicConditionalState,
        )
        
        logger.warning(f"Starting load process with supernodes {supernodes}.")
        self.paths_to_supernodes = self.load_supernodes_from_paths(supernodes)
        logger.warning(f"Supernodes are: {', '.join(str(x) for x in self.paths_to_supernodes.keys())}")
                
    def load_supernodes_from_paths(self, supernode_paths):   
        return {path: Supernode(path) for path in supernode_paths}
        
    def get_global_flags(self, state, utterance):
        # response types
        global_flags = {"GlobalFlag__" + k.name: v for k, v in global_response_type_dict(self, utterance).items()} 
        
        # abrupt initiative
        #global_flags.update(self.get_abrupt_initiative_flags())
        
        # custom activation logic
        global_flags.update(global_nlu.get_flags(self, state, utterance))
        
        logger.warning(f"GlobalFlags are: {global_flags}")
        
        return global_flags
        
    def get_next_supernode(self, state):
        next_supernode_path = 'FOOD__intro'
        return self.paths_to_supernodes[next_supernode_path]
        
                
    def get_response(self, state) -> ResponseGeneratorResult:
        logger.warning("Begin response for SymbolicResponseGenerator.")
        
        # Legacy response types
        
        self.state = state
        
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False
        
        # figure out what supernode we're in
        
        supernode_path = state.cur_supernode or 'GLOBALS'
        supernode = self.paths_to_supernodes[supernode_path]
        
        # TODO allow takeover
        
        logger.warning(f"Currently, we are in supernode {supernode}.")
            
        python_context = get_context_for_supernode(supernode)
        python_context.update({
            'rg': self,
            'state': state
        })
        
        # perform nlu
        
        flags = self.get_global_flags(state, utterance)
        flags.update(supernode.get_flags(self, state, utterance))
        
        logging.warning(f"Flags are: {flags}")
        logging.warning(f"Current entity is: {self.get_current_entity()}")
        
        # Process locals        
        contexts = {
            'flags': flags,
            'state': state,
        }
        locals = supernode.evaluate_locals(python_context, contexts)
        contexts['locals'] = locals
        logger.warning(f"Finished evaluating locals: {'; '.join((k + ': ' + v) for (k, v) in locals.items())}")
        
        locals['cur_entity'] = self.get_current_entity()

        # select subnode
        subnode = supernode.get_optimal_subnode(contexts=contexts)
        response = subnode.get_response(python_context, contexts)
        logger.warning(f'Received {response} from subnode {subnode}.')
        
        # update state
        state.data.update(supernode.get_state_updates())
        state.data.update(subnode.get_state_updates())
        
        # get next prompt
        next_supernode = self.get_next_supernode(state)
        prompt = next_supernode.get_prompt(python_context, contexts) # TODO fix contexts
        
        conditional_state = BaseSymbolicConditionalState(data=state.data,
            cur_supernode=next_supernode.name,                                                    
        )
    
        # TODO
        answer_type = AnswerType.QUESTION_SELFHANDLING
        
        return ResponseGeneratorResult(text=response + " " + prompt, 
                                       priority=ResponsePriority.STRONG_CONTINUE, 
                                       needs_prompt=False,
                                       state=state,
                                       cur_entity=None, 
                                       answer_type=answer_type,
                                       conditional_state=conditional_state
                                      )
        
        # post-subnode state updates
        # expose_vars = self.get_exposed_subnode_vars(supernode, subnode_name)
        # exposed_context = {}
        # if expose_vars is not None:
        #     for key in expose_vars:
        #         exposed_context[key] = eval(expose_vars[key], context)
        
        # select new supernode
        
        # return

    def update_state_if_chosen(self, state, conditional_state):
        """
        This method updates the internal state of the response generator,
        given that this RG is chosen as the next turn by the bot dialog manager. This state is accessible given
        the global state of the bot in the variable

        global_state['response_generator_states'][self.name]

        If the attribute value is NO_UPDATE: no update is done for that attribute.
        Otherwise, the attribute value is updated.
        If conditional_state is None: make no update other than saving the response types
        """
        response_types = self.get_cache(f'{self.name}_response_types')
        logger.info(f"Got cache for {self.name} response_types: {response_types}")
        if response_types is not None:
            state.response_types = construct_response_types_tuple(response_types)

        if conditional_state is None: return state

        if conditional_state:
            for attr in dir(conditional_state):
                if not callable(getattr(conditional_state, attr)) and not attr.startswith("__"):
                    val = getattr(conditional_state, attr)
                    if val != NO_UPDATE: setattr(state, attr, val)
        state.num_turns_in_rg += 1
        return state

    def update_state_if_not_chosen(self, state, conditional_state):
        """
        By default, this sets the prev_treelet_str and next_treelet_str to '' and resets num_turns_in_rg to 0.
        Response types are also saved.
        No other attributes are updated.
        All other attributes in ConditionalState are set to NO-UPDATE
        """
        response_types = self.get_cache(f'{self.name}_response_types')
        if response_types is not None:
            state.response_types = construct_response_types_tuple(response_types)

        state.prev_treelet_str = ''
        state.next_treelet_str = ''
        state.num_turns_in_rg = 0

        return state

    def set_user_attribute(self, attr_name, value):
        setattr(self.state_manager.user_attributes, attr_name, value)

    def get_user_attribute(self, attr_name, default):
        return getattr(self.state_manager.user_attributes, attr_name, default)
