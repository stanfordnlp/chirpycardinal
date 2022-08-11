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

        supernodes_path = f'chirpy/response_generators/{rg_folder_name}/yaml_files/supernodes/*/supernode.yaml'
        supernodes = glob.glob(supernodes_path, recursive=True)
        self.supernode_content = {}
        self.supernode_files = []
        for s in supernodes:
            supernode_name = s.split('/')[-2]
            self.supernode_files.append('/'.join(s.split('/')[:-1]))
            with open(s, "r") as stream:
                d = yaml.safe_load(stream)
                self.supernode_content[supernode_name] = d

        self.nlu_libraries = {}
        for name in self.supernode_content:
            nlu = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlu')
            self.nlu_libraries[name] = nlu

            # force all decorators to run by importing the nlg files, but we discard output
            if name != 'exit':
                dummy = import_module(f'chirpy.response_generators.{rg_folder_name}.yaml_files.supernodes.{name}.nlg_helpers')

        self.nlg_yamls = {}
        for path in self.supernode_files:
            node_name = path.split('/')[-1]
            if node_name == 'exit': continue
            nlg_yaml_file = os.path.join(path, 'nlg.yaml')
            with open(nlg_yaml_file, "r") as stream:
                d = yaml.safe_load(stream)
                self.nlg_yamls[node_name] = d

    def get_next_supernode(self, state):
        # Get matching next supernodes and return one sampled at random
        matching_supernodes = []
        for name in self.supernode_content:
            d = self.supernode_content[name]
            entry_reqs = d['requirements']
            for req_dict in entry_reqs:
                matches_entry_criteria = True
                for key in req_dict:
                    if state.__dict__[key] != req_dict[key]:
                        matches_entry_criteria = False
                        break

                if matches_entry_criteria:
                    matching_supernodes.append(name)
                    break

        if len(matching_supernodes) == 0: return None
        return random.choice(matching_supernodes)
        
    def lookup_value(self, value_name, contexts):
        if '.' in value_name:
            assert len(value_name.split('.')) == 2, "Only one namespace allowed."
            namespace_name, value_name = value_name.split('.')
            value = contexts[namespace_name][value_name]
            return value
            # if len(value_name.split('.')) == 2:
            #     namespace_name, value_name = value_name.split('.')
            #     value = contexts[namespace_name][value_name]
            #     return value
            # elif len(value_name.split('.')) == 3:
            #     namespace_name, value_name, attr_name = value_name.split('.')
            #     value = contexts[namespace_name][value_name].attr_name
            #     return value
        else:
            assert False, f"Need a namespace for entry condition {value_name}."

    def select_subnode(self, subnodes, contexts):
        for nlg in subnodes:
            entry_conditions = nlg['entry_conditions'] if 'entry_conditions' in nlg else {}
            for condition_name in entry_conditions:
                value = self.lookup_value(condition_name, contexts)
                target = entry_conditions[condition_name]
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

                if not passes_condition:
                    break
            else:
                logger.warning(f"Found NLG node: {nlg['node_name']}.")
                return nlg

        return None

    # def select_subnode(self, subnodes, contexts):
    #     for nlg in subnodes:
    #         entry_conditions = nlg['entry_conditions'] if 'entry_conditions' in nlg else {}
    #         for key in entry_conditions:
    #             key_to_behavior = {
    #                 'is_none': (lambda val: (val is None)),
    #                 'is_true': (lambda val: (val is True)),
    #                 'is_false': (lambda val: (val is False)),
    #                 'is_value': (lambda val, target: (val == target)),
    #             }
    #             assert key in key_to_behavior, f'Key not found: {key}.'
    #
    #             if key == 'is_value':
    #                 value_name = entry_conditions[key]['name']
    #                 value_target = entry_conditions[key]['value']
    #             else:
    #                 value_name = entry_conditions[key]
    #
    #             value = self.lookup_value(value_name, contexts)
    #             if key == 'is_value':
    #                 passes_condition = key_to_behavior[key](value, value_target)
    #             else:
    #                 passes_condition = key_to_behavior[key](value)
    #             if not passes_condition:
    #                 break
    #         else:
    #             logger.warning(f"Found NLG node: {nlg['node_name']}.")
    #             return nlg
    #
    #     return None
        
    def evaluate_nlg_call(self, data, context, contexts):
        if isinstance(data, str): # plain text
            return data

        if isinstance(data, bool): # boolean
            return data

        assert isinstance(data, dict) and len(data) == 1, f"Failure: data is {data}"
        type = next(iter(data))
        nlg_params = data[type]
        # logger.error(f"NLG_PARAM: {nlg_params} // TYPE: {type} // DATA: {data} // CONTEXT: {context}  ")
        if type == 'one of':
            assert isinstance(nlg_params, list)
            chosen = random.choice(nlg_params)['option']
            if isinstance(chosen, str):
                return chosen
            assert isinstance(nlg_params, list)
            return self.evaluate_nlg_calls(chosen, context, contexts)
        elif type == 'eval':
            assert isinstance(nlg_params, str)
            if nlg_params == 'None':
                return None
            elif nlg_params == 'True':
                return True
            elif nlg_params == 'False':
                return False
            else:
                return effify(nlg_params, global_context=context)
        elif type == 'val':
            assert isinstance(nlg_params, str)
            return self.lookup_value(nlg_params, contexts)
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
            neural_condition = self.evaluate_nlg_calls(nlg_params['condition'], context, contexts) if 'condition' in nlg_params else None
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
        for elem in datas:
            # logger.error(f"ELEM {elem}  // {self.evaluate_nlg_call(elem, context, contexts)}")
            output_str = str(self.evaluate_nlg_call(elem, context, contexts))
            output.append(output_str if output_str != 'None' else '')

        logger.error(f"DATAS: {datas} // OUTPUT: {output}")
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

    def get_subnode_updates(self, supernode, subnode_name):
        subnode_nlgs = self.nlg_yamls[supernode]['subnodes']
        for key in subnode_nlgs:
            logger.error(f"SBNDNGL: {key} // {subnode_name}")
        for nlg in subnode_nlgs:
            if nlg['node_name'] == subnode_name:
                if 'updates' not in nlg or nlg['updates'] == 'None': return None
                return nlg['updates']
        return None
        
    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        logger.primary_info(f'{self.name} - Get response')
        state, utterance, response_types = self.get_state_utterance_response_types()
        needs_prompt = False

        cur_supernode = state.cur_supernode
        if state.cur_supernode is None:
            logger.error(f"STATE BEFORE CHECK & SET: {state}")
            state = self.rg.check_and_set_entry_conditions(state)
            logger.error(f"STATE AFTER CHECK & SET: {state}")
            cur_supernode = self.get_next_supernode(state)

        context = get_context_for_supernode(cur_supernode)
        context.update({
            'rg': self.rg,
            'state': state
        })

        # Intent processing
        nlu = self.nlu_libraries[cur_supernode]
        flags = nlu.nlu_processing(self.rg, state, utterance, response_types)
        
        # context = get_context_for_supernode(cur_supernode)
        #
        # logger.error(f" line 225 {context}")

        nlg_data = self.nlg_yamls[cur_supernode]
        logger.warning(f"NLG data keys: {nlg_data}")

        # Process locals        
        locals = {}
        contexts = {
            'flags': flags,
            'locals': locals,
            'state': state,
        }
        if 'locals' in nlg_data:
            for local_key, local_values in nlg_data['locals'].items():
                logger.error(f"*** {local_key} // {local_values}")
                if isinstance(local_values, dict):
                    locals[local_key] = self.evaluate_nlg_calls([local_values], context, contexts)
                    if isinstance(local_values, dict) and next(iter(local_values)) == 'entity_name':
                        locals[local_key] = get_entity_by_wiki_name(locals[local_key])
                        assert isinstance(locals[local_key], WikiEntity)
                else:
                    locals[local_key] = self.evaluate_nlg_calls(local_values, context, contexts)

        logger.primary_info(f"Finished evaluating locals: {'; '.join((k + ': ' + str(v)) for (k, v) in locals.items())}")
        # Select subnode
        #def select_subnode(self, subnodes, flags, locals, state)

        logger.error(f"SUBNODE NLG DATA: {nlg_data}")
        subnode_data = self.select_subnode(subnodes=nlg_data['subnodes'],
                                           contexts=contexts)
        assert subnode_data is not None, f"There was no matching subnode in the supernode {cur_supernode}."

        # Process subnode
        subnode_name = subnode_data['node_name']
        structured_response = subnode_data['response']
        response = self.evaluate_nlg_calls(structured_response, context, contexts)
        
        logger.warning(f'Received {response} from symbolic treelet.')

        # post-subnode state updates
        updates = self.get_subnode_updates(cur_supernode, subnode_name)


        # if 'subnode_state_updates' in self.supernode_content[cur_supernode]:
        #     subnode_state_updates = self.supernode_content[cur_supernode]['subnode_state_updates'][subnode_name]
        # else:
        #     subnode_nlgs = self.nlg_yamls[cur_supernode]
        #     for nlg in subnode_nlgs['response']:
        #         if nlg['node_name'] == subnode_name:
        #             if 'set_state' in nlg:
        #                 self.subnode_state_updates = nlg['set_state']
        #         else:
        #             assert False
        #     else:
        #         assert False
            
        # if subnode_state_updates == 'None': subnode_state_updates = {}
        global_post_state_updates = self.supernode_content[cur_supernode]['global_post_supernode_state_updates']
        if global_post_state_updates == 'None': global_post_state_updates = {}
        # assert isinstance(subnode_state_updates, dict), f"subnode_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"
        assert isinstance(global_post_state_updates, dict), f"global_post_state_updates of {subnode_name} in {cur_supernode} needs to be a dict or None"

        logger.error(f"GLOBAL_POST_STATE_UPDATE: {global_post_state_updates}")

        # logger.error(f"SUBNODE_STATE_UPDATE: {subnode_state_updates}")
        # subnode_state_updates.update(global_post_state_updates)
        updates.update(global_post_state_updates)
        logger.error(f"UPDATES ALL: {updates}")

        result = ResponseGeneratorResult(text=response, priority= ResponsePriority.NO, needs_prompt=None, state=None, cur_entity=None)
        result_conditional_state = self.state_module.ConditionalState()
        for update_attr in updates:
            update_val = self.evaluate_nlg_call(updates[update_attr], context, contexts)
            if update_attr.startswith("state."):
                setattr(result_conditional_state, update_attr, update_val)
            else:
                setattr(result, update_attr, update_val)

        setattr(result, 'conditional_state', result_conditional_state)
        logger.error(f'RESULT: {result}')

        # if 'priority' in subnode_state_updates:
        #     priority_context = dict(context_updates)
        #     priority_context.update(globals())
        #     priority_context.update(context)
        #     priority = eval(subnode_state_updates['priority'], priority_context)
        #     assert isinstance(priority, ResponsePriority)
        #     del subnode_state_updates['priority']
        # if 'needs_prompt' in subnode_state_updates:
        #     needs_prompt = eval(str(subnode_state_updates['needs_prompt']), context)
        #     assert type(needs_prompt) == type(True) # make sure it is a boolean
        #     del subnode_state_updates['needs_prompt']
        # else:
        #     needs_prompt = False
        #
        # if 'cur_entity' in subnode_state_updates:
        #     cur_entity = eval(subnode_state_updates['cur_entity'], context)
        #     assert cur_entity is None or isinstance(cur_entity, WikiEntity), f"error on {cur_entity}, eval string {subnode_state_updates['cur_entity']}"
        #     del subnode_state_updates['cur_entity']
        # else:
        #     cur_entity = None
        #
        # if 'answer_type' in subnode_state_updates:
        #     answer_context = dict(context_updates)
        #     answer_context.update(globals())
        #     answer_context.update(context)
        #     answer_type = eval(subnode_state_updates['answer_type'], answer_context)
        #     assert isinstance(answer_type, AnswerType)
        #     del subnode_state_updates['answer_type']
        # else:
        #     answer_type = AnswerType.NONE
        #
        # for key in subnode_state_updates:
        #     if type(subnode_state_updates[key]) != type(True):
        #         # eval non boolean flags
        #         subnode_state_updates[key] = eval(subnode_state_updates[key], context)
        # subnode_state_updates['prompt_treelet'] = self.name
        # subnode_state_updates['prev_treelet_str'] = self.name
        #
        # logger.error(f"SUBNODE_STATE_UPDATES AFTER UPDATES: {subnode_state_updates}")
        # return ResponseGeneratorResult(text=response, priority=priority, needs_prompt=needs_prompt, state=state,
        #                                cur_entity=cur_entity, answer_type=answer_type,
        #                                conditional_state=self.state_module.ConditionalState(**subnode_state_updates))

        return result


    def get_prompt(self, conditional_state=None):
        state, utterance, response_types = self.get_state_utterance_response_types()

        if getattr(conditional_state, 'prompt_treelet', NO_UPDATE) == NO_UPDATE:
            # no prompt_treelet given. Respond with unconditional prompt
            prompting_supernodes = []
            for supernode_name in self.supernode_content:
                # ORDER MATTERS
                content = self.supernode_content[supernode_name]
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
                    
                    prompt_text = effify(prompt_text, context)
                    prompt_state_updates = self.supernode_content[supernode_name]['unconditional_prompt_updates'][case_name]
                    if prompt_state_updates == 'None': prompt_state_updates = {}
                    if 'prompt_type' in prompt_state_updates:
                        prompt_type = eval(str(prompt_state_updates['prompt_type']), context)
                        assert isinstance(prompt_type, PromptType)
                        del prompt_state_updates['prompt_type']
                    else:
                        prompt_type = PromptType.CONTEXTUAL

                    logger.info(f'chungus {prompt_text}')
                    return PromptResult(text=prompt_text, prompt_type=prompt_type, state=state, cur_entity=None,
                            conditional_state=self.state_module.ConditionalState(**prompt_state_updates))

            return None

        cur_supernode = self.get_next_supernode(conditional_state)
        print('prompt treelet to {}'.format(cur_supernode))
        if cur_supernode is None or conditional_state is None or cur_supernode == 'exit':
            # next_treelet_str, question = self.get_next_treelet()
            return None

        function_cache = get_context_for_supernode(cur_supernode)

        prompt = self.supernode_content[cur_supernode]['prompt']
        if prompt == 'None':
            prompt = []
        elif 'call_method' in prompt:
            method_name = prompt['call_method']
            if method_name not in function_cache:
                logger.error(f"Function {method_name} declared in yaml file not defined in function cache")
                raise KeyError(f'NLG helpers function cache error {method_name}')
            func = function_cache[method_name]
            conditional_state.cur_supernode = cur_supernode
            return func(self.rg, conditional_state)

        prompt_texts = []
        for i in range(len(prompt)):
            case = prompt[i]
            requirements = case['required']
            if requirements == 'None': requirements = {}
            assert isinstance(requirements, dict), f"requirements in prompt (supernode {cur_supernode}) needs to define a dict or None"
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
                prompt_text = effify(case['prompt'], context)
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

