import logging
import random
import glob
import yaml
import os
from importlib import import_module

from chirpy.core.util import infl
from chirpy.core.response_generator import Treelet, get_context_for_supernode
from chirpy.core.response_priority import ResponsePriority
from chirpy.core.response_generator.state import NO_UPDATE
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.entity_linker.entity_linker_simple import get_entity_by_wiki_name

from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult, PromptType, AnswerType
from chirpy.core.response_generator.response_type import ResponseType

logger = logging.getLogger('chirpylogger')


import inflect
engine = inflect.engine()


def effify(non_f_str: str, global_context: dict):
    logger.primary_info(f"Outside eval, global_context is {str(global_context.keys())}, non f str is {non_f_str}")
    return eval(non_f_str, global_context)

class GodTreelet(Treelet):
    def __init__(self, rg, rg_folder_name):
        super().__init__(rg)
        self.name = 'god_treelet'
        self.can_prompt = True

        self.state_module = import_module(f'chirpy.response_generators.{rg_folder_name}.state')

        supernodes_path = f'chirpy/response_generators/{rg_folder_name}/yaml_files/supernodes/*/nlg.yaml'
        supernodes = glob.glob(supernodes_path, recursive=True)
        self.nlg_yamls = {}
        self.supernode_files = []
        for s in supernodes:
            self.supernode_files.append('/'.join(s.split('/')[:-1]))
            supernode_name = s.split('/')[-2]
            with open(s, "r") as stream:
                d = yaml.safe_load(stream)
                self.nlg_yamls[supernode_name] = d

        self.nlu_libraries = {}
        for name in self.nlg_yamls:
            nlu = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlu')
            self.nlu_libraries[name] = nlu
            # force all decorators to run by importing the nlg files, but we discard output
            if name != 'exit':
                dummy = import_module(
                    f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlg_helpers')


        self.nlu_handlers = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.handlers.nlu')

        handlers_path = f'chirpy/response_generators/{rg_folder_name}/yaml_files/handlers/nlg.yaml'
        with open(handlers_path , "r") as stream:
            h = yaml.safe_load(stream)
        self.nlg_handlers = h

        self.handler_helpers = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.handlers.handler_helpers')



    def get_next_supernode(self, state):
        # Get matching next supernodes and return one sampled at random
        matching_supernodes = []
        for name in self.nlg_yamls:
            d = self.nlg_yamls[name]
            entry_reqs = d['requirements']
            for req_dict in entry_reqs:
                matches_entry_criteria = True
                for key in req_dict:
                    assert key.startswith("state."), "The requirement for supernode should be a state."
                    state_name = key[len("state."):]
                    if state.__dict__[state_name] != req_dict[key]:
                        matches_entry_criteria = False
                        break

                if matches_entry_criteria:
                    matching_supernodes.append(name)
                    break

        if len(matching_supernodes) == 0: return None
        return random.choice(matching_supernodes)
        
    def lookup_value(self, value_name, contexts):
        if '.' in value_name:
            assert len(value_name.split('.')) == 2 or len(value_name.split('.')) == 3, "Only one namespace with 0 - 1 attributes allowed."
            if len(value_name.split('.')) == 2:
                namespace_name, value_name = value_name.split('.')
                if isinstance(contexts[namespace_name], dict):
                    value = contexts[namespace_name][value_name]
                else:
                    value = getattr(contexts[namespace_name], value_name)
                return value
            elif len(value_name.split('.')) == 3:
                namespace_name, value_name, attr_name = value_name.split('.')
                value = getattr(getattr(contexts[namespace_name], value_name), attr_name)
                return value
            assert False, f"Need a namespace for entry condition {value_name}."

    def select_subnode(self, subnodes, contexts):
        for nlg in subnodes:
            if 'response_entry_conditions' in nlg:
                entry_conditions = nlg['response_entry_conditions']
            elif 'prompt_entry_conditions' in nlg:
                entry_conditions = nlg['prompt_entry_conditions']
            elif 'handler_entry_conditions' in nlg:
                entry_conditions = nlg['handler_entry_conditions']
            else:
                entry_conditions = {}

            for condition_name in entry_conditions:
                value = self.lookup_value(condition_name, contexts)
                target = entry_conditions[condition_name]
                if type(target) == bool:
                    value = bool(value)
                logger.error(f"CHECK: {condition_name} // {value} // {target}")
                check_behavior = {
                    'None': (lambda val: (val is None)),
                    'True': (lambda val: (val is True)),
                    'False': (lambda val: (val is False)),
                    'Value': (lambda val, target: (val == target)),
                }
                if target in ['None', 'True', 'False']:
                    passes_condition = check_behavior[target](value)
                else:
                    passes_condition = check_behavior['Value'](value, target)
                logger.error(passes_condition)
                if not passes_condition:
                    break
            else:
                if 'response_node_name' in nlg:
                    logger.warning(f"Found NLG node: {nlg['response_node_name']}.")
                elif 'prompt_node_name' in nlg:
                    logger.warning(f"Found NLG node: {nlg['prompt_node_name']}.")
                elif 'handler_node_name' in nlg:
                    logger.warning(f"Found NLG node: {nlg['handler_node_name']}.")
                return nlg

        return None
        
    def evaluate_nlg_call(self, data, context, contexts):
        if isinstance(data, str): # plain text
            return data
        if isinstance(data, bool): # boolean
            return data

        assert isinstance(data, dict) and len(data) == 1, f"Failure: data is {data}"
        type = next(iter(data))
        nlg_params = data[type]
        if type == 'one of':
            assert isinstance(nlg_params, list)
            chosen = random.choice(nlg_params)['option']
            if isinstance(chosen, str):
                return chosen
            assert isinstance(nlg_params, list)
            return self.evaluate_nlg_calls(chosen, context, contexts)
        elif type == 'eval':
            assert isinstance(nlg_params, str)
            return effify(nlg_params, global_context=context)
        elif type == 'val':
            assert isinstance(nlg_params, str)
            return self.lookup_value(nlg_params, contexts)
        elif type == 'const':
            assert isinstance(nlg_params, str)
            if nlg_params.isdigit():
                return int(nlg_params)
            elif nlg_params == 'None':
                return None
        elif type == 'nlg_helper':
            assert isinstance(nlg_params, dict)
            function_name = nlg_params['name']
            assert function_name in context
            nlg_args = [self.lookup_value(nlg_args, contexts) for nlg_args in nlg_params.get('args', [])]
            args = [self.rg] + nlg_args   # Add RG as first argument
            return context[function_name](*args)
        elif type == 'inflect':
            assert isinstance(nlg_params, dict)
            inflect_token = nlg_params['inflect_token']
            inflect_entity = self.lookup_value(nlg_params['inflect_entity'], contexts)
            assert isinstance(inflect_entity, WikiEntity)
            inflect_plural = inflect_entity.is_plural
            if 'inflect_form' in nlg_params.keys():
                inflect_form = nlg_params['inflect_form'].split(',')
                return inflect_form[1] if inflect_plural else inflect_form[0]
            return infl(inflect_token, inflect_plural)
        elif type == 'inflect_helper':
            assert isinstance(nlg_params, dict)
            inflect_function = nlg_params['type']
            inflect_input = self.evaluate_nlg_call(nlg_params['str'], context, contexts)
            return getattr(engine, inflect_function)(inflect_input)
        elif type == 'entity_name':
            assert isinstance(nlg_params, str)
            entity = context['rg'].get_current_entity()
            assert isinstance(entity, WikiEntity)
            return entity.name
        elif type == 'neural_generation':
            assert isinstance(nlg_params, dict)
            neural_prefix = self.evaluate_nlg_calls(nlg_params['prefix'], context, contexts) if 'prefix' in nlg_params else None
            neural_condition = [self.evaluate_nlg_call(nlg_params['condition'], context, contexts)] if 'condition' in nlg_params else None
            neural_fallback = self.evaluate_nlg_calls(nlg_params['fallback'], context, contexts) if 'fallback' in nlg_params else None
            neural_response = self.get_neural_response(prefix=neural_prefix, conditions=neural_condition)
            if neural_response:
                neural_suffix = self.evaluate_nlg_calls(nlg_params['suffix'], context, contexts) if 'suffix' in nlg_params else ""
                return neural_response + neural_suffix
            elif neural_fallback:
                return neural_fallback
            else:
                return ""
        else:
            assert False, f"Generation type {type} not found!"

    def evaluate_nlg_calls(self, datas, context, contexts):
        output = []
        if isinstance(datas, str):
            return self.evaluate_nlg_call(datas, context, contexts)
        if isinstance(datas, dict):
            datas = [datas]
        for elem in datas:
            output_str = str(self.evaluate_nlg_call(elem, context, contexts))
            output.append(output_str if output_str != 'None' else '')

        logger.primary_info(f"evaluate_nlg_calls is called on {datas}. The output list generated is {output}.")
        return ' '.join(output)

    def get_unconditional_prompt_text(self, flags, supernode):
        for cases in self.nlg_yamls[supernode]['unconditional_prompt']:
            requirements = cases['entry_conditions']
            matches_entry_criteria = True
            for key in requirements:
                if flags[key] != requirements[key]:
                    matches_entry_criteria = False
                    break
            if matches_entry_criteria:
                return cases['case_name'], cases['prompt']
        return None

    def get_local_post_subnode_updates(self, supernode, subnode_name, context, contexts):
        subnode_updates = {}
        subnode_nlgs = self.nlg_yamls[supernode]['response_subnodes']
        for nlg in subnode_nlgs:
            if nlg['response_node_name'] == subnode_name:
                if 'local_post_subnode_updates' not in nlg or nlg['local_post_subnode_updates'] == 'None': break
                for key in nlg['local_post_subnode_updates']:
                    if key == 'priority' or key == 'answer_type':
                        subnode_updates[key] == nlg['local_post_subnode_updates'][key]
                    elif isinstance(nlg['local_post_subnode_updates'][key], str):
                        subnode_updates[key] = eval(nlg['local_post_subnode_updates'][key], context)
                    else:
                        subnode_updates[key] = self.evaluate_nlg_call(nlg['local_post_subnode_updates'][key], context, contexts)
        return subnode_updates

    def get_global_post_supernode_updates(self, supernode, context,contexts):
        supernode_updates = self.nlg_yamls[supernode]['global_post_supernode_updates']
        for key in supernode_updates.keys():
            if isinstance(supernode_updates[key], str) and key != 'priority' and key != 'answer_type':
                supernode_updates[key] = eval(supernode_updates[key], context)
            elif isinstance(supernode_updates[key], dict):
                supernode_updates[key] = self.evaluate_nlg_call(supernode_updates[key], context, contexts)
        return supernode_updates
        
    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False

        cur_supernode = state.cur_supernode
        if state.cur_supernode is None:
            state = self.rg.check_and_set_entry_conditions(state)
            cur_supernode = self.get_next_supernode(state)

        context = get_context_for_supernode(cur_supernode)
        context.update({
            'rg': self.rg,
            'state': state
        })

        # Intent processing
        nlu = self.nlu_libraries[cur_supernode]
        handler_flags = self.nlu_handlers.handler_nlu_processing(self.rg, self.rg.state_manager)
        response_flags = nlu.response_nlu_processing(self.rg, state, utterance, response_types)

        nlg_data = self.nlg_yamls[cur_supernode]
        logger.warning(f"NLG data keys: {nlg_data}")

        handler_data = self.nlg_handlers

        # Process locals & entities
        response_locals = {}
        response_entities = {}
        contexts = {
            'response_flags': response_flags,
            'handler_flags': handler_flags,
            'response_locals': response_locals,
            'state': state,
            'response_entities': response_entities,
        }

        cur_entity = self.evaluate_nlg_calls([{'entity_name': 'rg.get_current_entity()'}], context, contexts)
        cur_entity = get_entity_by_wiki_name(cur_entity) if cur_entity != 'None' else None
        contexts['response_entities']['cur_entity'] = cur_entity
        contexts['response_entities']['lowercased_cur_entity'] = cur_entity.talkable_name.lower() if cur_entity else None

        logger.primary_info(f"Finished evaluating entities: {'; '.join((k + ': ' + str(v)) for (k, v) in response_entities.items())}")

        if 'response_locals' in nlg_data:
            for local_key, local_values in nlg_data['response_locals'].items():
                if isinstance(local_values, dict):
                    response_locals[local_key] = self.evaluate_nlg_calls([local_values], context, contexts)
                else:
                    response_locals[local_key] = self.evaluate_nlg_calls(local_values, context, contexts)

        logger.primary_info(f"Finished evaluating locals: {'; '.join((k + ': ' + str(v)) for (k, v) in response_locals.items())}")

        # Select subnode
        handler_subnode_data = self.select_subnode(subnodes=handler_data['handler_subnodes'],
                                           contexts=contexts)
        if handler_subnode_data:
            logger.primary_info(f"Select {handler_subnode_data['handler_node_name']} as handler_subnode.")
        else:
            logger.primary_info("No abrupt high initiative")

        if handler_subnode_data is not None:
            handler_response = handler_subnode_data['response_generator_result']
            if 'call_method' in handler_response:
                method_name = handler_response['call_method']
                flag = list(handler_subnode_data['handler_entry_conditions'].keys())[0][len('handler_flags.'):]
                slots = handler_flags[flag]
                func = getattr(self.handler_helpers, method_name)
            return func(self.rg, slots)

        subnode_data = self.select_subnode(subnodes=nlg_data['response_subnodes'],
                                           contexts=contexts)
        assert subnode_data is not None, f"There was no matching subnode in the supernode {cur_supernode}."

        # Process subnode
        subnode_name = subnode_data['response_node_name']
        structured_response = subnode_data['response']
        response = self.evaluate_nlg_calls(structured_response, context, contexts)
        
        logger.warning(f'Received {response} from symbolic treelet.')

        # post-subnode updates
        post_subnode_updates = self.get_local_post_subnode_updates(cur_supernode, subnode_name, context, contexts)
        context.update(post_subnode_updates)

        global_post_supernode_updates = self.get_global_post_supernode_updates(cur_supernode, context, contexts)
        if global_post_supernode_updates == 'None': global_post_supernode_updates = {}

        assert isinstance(post_subnode_updates, dict), f"subnode_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"
        assert isinstance(global_post_supernode_updates, dict), f"global_post_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"

        post_subnode_updates.update(global_post_supernode_updates)

        # Create ResponseGeneratorResult
        result = ResponseGeneratorResult(text=response, priority=priority, needs_prompt=False,
                                       state=state, cur_entity=None, answer_type=AnswerType.NONE,
                                       conditional_state=None)

        state_updates = {}
        attr_context = context
        attr_context.update(globals())
        attr_context.update({'priority': priority})
        for attr in post_subnode_updates:
            if attr.startswith('state.'):
                state_updates[attr[len('state.'):]] = post_subnode_updates[attr]
            else:
                attr_val = eval(str(post_subnode_updates[attr]), attr_context)
                assert attr in result.__dict__.keys()
                setattr(result, attr, attr_val)

        state_updates['prompt_treelet'] = self.name
        state_updates['prev_treelet_str'] = self.name

        setattr(result, 'conditional_state', self.state_module.ConditionalState(**state_updates))

        return result

    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if getattr(conditional_state, 'prompt_treelet', NO_UPDATE) == NO_UPDATE:
            # no prompt_treelet given. Respond with unconditional prompt
            prompting_supernodes = []
            for supernode_name in self.nlg_yamls:
                # ORDER MATTERS
                content = self.nlg_yamls[supernode_name]
                if 'unconditional_prompt_updates' in content:
                    prompting_supernodes.append((supernode_name, content['prompt_ranking']))

            prompt_supernodes_by_rank = sorted(prompting_supernodes, key=lambda x: x[1])
            for supernode_name, _ in prompt_supernodes_by_rank:
                nlu = self.nlu_libraries[supernode_name]
                flags = nlu.prompt_nlu_processing(self.rg, state, utterance, response_types)
                prompt_res = self.get_unconditional_prompt_text(flags, supernode_name)
                if prompt_res:
                    case_name, prompt_text = prompt_res

                    cntxt = get_context_for_supernode(supernode_name)
                    context = {
                        'rg': self.rg,
                        'state': state
                    }
                    context.update(cntxt)
                    context.update(globals())
                    
                    # prompt_text = effify(prompt_text, context)
                    prompt_text = self.evaluate_nlg_calls(prompt_text, context, context)
                    prompt_state_updates = self.nlg_yamls[supernode_name]['unconditional_prompt_updates'][case_name]
                    if prompt_state_updates == 'None': prompt_state_updates = {}
                    if 'prompt_type' in prompt_state_updates:
                        prompt_type = eval(str(prompt_state_updates['prompt_type']), context)
                        assert isinstance(prompt_type, PromptType)
                        del prompt_state_updates['prompt_type']
                    else:
                        prompt_type = PromptType.CONTEXTUAL
                    return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=None,
                            conditional_state=self.state_module.ConditionalState(**prompt_state_updates))
            return None

        cur_supernode = self.get_next_supernode(conditional_state)
        print('prompt treelet to {}'.format(cur_supernode))

        if cur_supernode is None or conditional_state is None or cur_supernode == 'exit':
            # next_treelet_str, question = self.get_next_treelet()
            return None

        # TODO: This part of code will be replaced by prompt_subnodes architecture.
        if 'prompt' in self.nlg_yamls[cur_supernode]:
            prompt = self.nlg_yamls[cur_supernode]['prompt']
            function_cache = get_context_for_supernode(cur_supernode)
            if prompt == 'None':
                prompt = []
            elif 'call_method' in prompt:
                method_name = prompt['call_method']
                if method_name not in function_cache:
                    raise KeyError(f'NLG helpers function cache error {method_name}')
                func = function_cache[method_name]
                conditional_state.cur_supernode = cur_supernode
                return func(self.rg, conditional_state)

            prompt_texts = []
            for i in range(len(prompt)):
                case = prompt[i]
                requirements = case['required']
                if requirements == 'None': requirements = {}
                assert isinstance(requirements,
                                  dict), f"requirements in prompt (supernode {cur_supernode}) needs to define a dict or None"
                matches_entry_criteria = True
                for key in requirements:
                    if conditional_state.__dict__[key] != requirements[key]:
                        matches_entry_criteria = False
                        break
                if matches_entry_criteria:
                    context = get_context_for_supernode(cur_supernode)
                    cntxt = {
                        'rg': self.rg,
                        'state': conditional_state
                    }
                    context.update(cntxt)
                    # prompt_text = effify(case['prompt'], context)
                    prompt_text = self.evaluate_nlg_calls(case['prompt_text'], context, context)
                    prompt_texts.append(prompt_text)

            entity = self.rg.state_manager.current_state.entity_tracker.cur_entity

            text = ''
            if len(prompt_texts) > 0:
                text = random.choice(prompt_texts)

            conditional_state.cur_supernode = cur_supernode
            prompt_type = PromptType.NO if text == '' else PromptType.CONTEXTUAL
            if text == '': print('no prompt')

            # YAML processing for prompt treelet leading question
            return PromptResult(text=text, prompt_type=prompt_type, state=state, cur_entity=entity,
                                conditional_state=conditional_state)


        # Get prompt from prompt_subnodes architecture

        entity = self.rg.state_manager.current_state.entity_tracker.cur_entity
        conditional_state.cur_supernode = cur_supernode

        prompt_result = PromptResult(text="", state=state, cur_entity=entity,
                                     answer_type=AnswerType.QUESTION_SELFHANDLING,
                                     prompt_type=PromptType.NO,
                                     conditional_state=conditional_state)

        prompt_subnodes = self.nlg_yamls[cur_supernode]['prompt_subnodes']
        logger.warning(f"prompt_subnodes: {prompt_subnodes}")

        if prompt_subnodes != 'None':
            nlu = self.nlu_libraries[cur_supernode]
            prompt_flags = nlu.prompt_nlu_processing(self.rg, conditional_state)

            prompt_contexts = {
                'prompt_flags': prompt_flags,
            }

            prompt_subnode_data = self.select_subnode(subnodes=prompt_subnodes,
                                                             contexts=prompt_contexts)
            assert prompt_subnode_data is not None, f"There was no matching prompt subnode in the supernode {cur_supernode}."

            prompt_subnode_name = prompt_subnode_data['prompt_node_name']
            structured_prompt = prompt_subnode_data['prompt']
            logger.info(f'{prompt_subnode_name} is selected.')

            context = get_context_for_supernode(cur_supernode)
            cntxt = {
                'rg': self.rg,
                'state': conditional_state
            }
            context.update(cntxt)

            prompt_text = self.evaluate_nlg_calls(structured_prompt, context, context)
            setattr(prompt_result, 'text', prompt_text)

            logger.warning(f'Received prompt: {prompt_text}.')

            if 'prompt_type' in prompt_subnode_data:
                setattr(prompt_result, 'prompt_type', prompt_subnode_data['prompt_type'])
            else:
                setattr(prompt_result, 'prompt_type', PromptType.CONTEXTUAL)

            if 'answer_type' in prompt_subnode_data:
                setattr(prompt_result, 'answer_type', prompt_subnode_data['answer_type'])

        if getattr(prompt_result, 'text') == '':
            print('no prompt')

        return prompt_result