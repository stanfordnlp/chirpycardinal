from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult, PromptType
from chirpy.response_generators.wiki2.state import ConditionalState, State, CantPromptError, CantRespondError
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.util import filter_and_log
import random
from copy import deepcopy
from chirpy.response_generators.wiki2.wiki_utils import WikiSection
from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
import editdistance
import chirpy.core.offensive_classifier.offensive_classifier

logger = logging.getLogger('chirpylogger')

class DiscussSectionTreelet(Treelet):
    """
    Discuss a specific Wiki section
    """
    name = "wiki_discuss_section_treelet"

    def get_selected_section(self, sections):
        """
        Get the section that the user says they want to talk about
        :param sections: possible sections
        :return:
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        state = self.rg.state
        entity = state.cur_entity

        for option in state.prompted_options:
            # CC: removed all(). 'musical style' -- 'style' did not match
            if any(editdistance.eval(u_token, eu_token) < 2 for u_token in utterance.split(' ')
                   for eu_token in option.lower().split(' ')):
                logger.primary_info(f'WIKI prompted {option} and successfully found it in user utterance')
                # In case the prompted option was for 1st level section, but actually the second level section was suggested,
                # run the following code to get the right option.

                # While we expect the option selected from prompted_options to have been chosen,
                # In the case of an entity switching (entity_a -> entity_b -> entity_a),
                # the prompted options are from a entity_b but the suggested sections are from entity_a
                options = [sec for sec in state.entity_state[entity.name].suggested_sections if option in str(sec)]
                if options:
                    option = options[0].title
                    break
        else:
            #Check if any section title directly matches (TODO: remove replicated code in any_section_title_matches)
            for section in sections:
                if any(editdistance.eval(u_token, eu_token) < 2 for u_token in utterance.split(' ')
                       for eu_token in section.title.lower().split(' ')):
                    option = section.title
                    logger.primary_info(f'WIKI found successfully section title {option} in user utterance')
                    break
            else:
                #If we see many users talking about random things, we should use search_sections here
                # elif: yes in user utterance then pick the first section, but no section is specifically mentioned
                if ResponseType.YES in response_types:
                    if state.prompted_options:
                        option = state.prompted_options[0]
                        # In case the prompted option was for 1st level section, but actually the second level section was suggested,
                        # run the following code to get the right option
                        new_options = [sec for sec in state.entity_state[entity.name].suggested_sections if option in str(sec)]
                        new_option = new_options[0].title if new_options else None
                        if new_option and new_option != option:
                            logger.primary_info(f'WIKI detected user saying yes to section {option}, but the prompted section was actually {new_option}. Responding using that.')
                            option = new_option
                        else:
                            logger.primary_info(f'WIKI detected user saying yes to section {option}, responding to that section')
                    else:
                        logger.primary_info("User did not reply to open prompt with anything specific to talk about")
                        return None
                else:
                    option = None
        return option

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        """
        This method will attempt to select a section to talk about given the user's utterance
        which we assume is neither yes or no.
        """
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = state.cur_entity

        if not entity or entity.name not in state.entity_state:
            raise CantRespondError("Recommended entity has changed")
        sections = wiki_utils.get_wiki_sections(entity.name)

        # Check if there is high fuzzy overlap between prompted options and user utterance, if so, pick that section
        #Prepared apology response
        apology_state = deepcopy(state)
        apology_state.entity_state[entity.name].finished_talking = True

        option = self.get_selected_section(sections)

        if option:
            selected_sections = [sec for sec in sections if sec.title == option]
            if len(selected_sections) == 0:
                CantRespondError(f"Selected option {option} doesn't correspond to a section title, but it should!\n"
                                 f"Sections are {sections}")
            selected_section = selected_sections[0]
            logger.error(f"Selected section: {selected_section}")
            # This should not throw an error because there should at least be one suggested section that matches the option
            section_summary = selected_section.summarize(self.rg.state_manager, max_sents=3)
            logger.error(f"Selected section summary: {section_summary}")
            section_summary = wiki_utils.check_section_summary(self.rg, section_summary, selected_section)
            logger.error(f"After check: {section_summary}")
            if section_summary:
                conditional_state = ConditionalState(cur_doc_title=entity.name,
                                                     discussed_section=selected_section,
                                                     prev_treelet_str=self.name,
                                                     next_treelet_str=self.rg.discuss_section_further_treelet.name
                                                     )
                if entity.name not in selected_section.title:
                    entitys_section = f"{entity.name}'s {selected_section.title}"
                else:
                    entitys_section = f"the {selected_section.title}"

                prefix = random.choice([
                    f"So, about {entitys_section}, ",
                    f"Great, so regarding {entitys_section}, "
                ])
                return ResponseGeneratorResult(text=prefix + section_summary, priority=ResponsePriority.STRONG_CONTINUE,
                                               needs_prompt=False, state=state, cur_entity=entity,
                                               conditional_state=conditional_state)
            else:
                logger.primary_info("Failed to generate a valid summary for the WikiSection")
                return self.emptyResult()
        else:
            logger.primary_info(f"Found no sections matching user utterance. Can't respond with sections")
            return self.emptyResult()
