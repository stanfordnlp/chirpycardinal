from copy import deepcopy

import editdistance
import logging
import random

from typing import Tuple, Optional, List

import chirpy.core.offensive_classifier.offensive_classifier
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.latency import measure
from chirpy.core.offensive_classifier.offensive_classifier import contains_offensive
from chirpy.response_generators.wiki.treelets.abstract_treelet import Treelet, HANDOVER_TEXTS
from chirpy.response_generators.wiki.dtypes import State, CantContinueResponseError, ConditionalState, CantRespondError, \
    CantPromptError
from chirpy.core.response_generator_datatypes import ResponseGeneratorResult, PromptResult
from chirpy.core.response_priority import ResponsePriority, PromptType
from chirpy.core.util import filter_and_log

import chirpy.response_generators.wiki.wiki_utils as wiki_utils
from chirpy.response_generators.wiki.wiki_utils import WikiSection

logger = logging.getLogger('chirpylogger')

# We want to acknowledge that we don't know much about what the user has just said before moving on.
APOLOGY_TEXTS = ["Hmm, that does sound interesting. But I don\'t know much about that.",
                 "Hmm, that is interesting. Unfortunately I don\'t know a lot about that."]


#First time Handle Section Treelet Prompts
def section_prompt_text(entity: str, sections:List[str], repeat=False):
    if repeat:
        section_choices = f"{sections[0]} and {sections[1]}" if len(sections) >= 2 else f"{sections[0]}"
        prompts = [f"We could also talk about {section_choices}.",
                   f"I think {entity}'s {section_choices} {'are' if len(sections)>=2 else 'is'} pretty interesting too. Wanna hear about {'them' if len(sections)>=2 else 'it'}?",
                   f"{section_choices} are pretty interesting. Do you want to hear more about {'them' if len(sections)>=2 else 'it'}?"]
    else:
        entitys = f"{entity}'s"
        section_choices = f"{sections[0]}, {sections[1]} or anything else" if len(sections)>=2 else f"{sections[0]}"
        section_choices_without_anything_ending = f"{sections[0]}"
        if len(sections) == 2:
            section_choices_without_anything_ending = f"{sections[0]} and {sections[1]}"
        elif len(sections)>= 3:
            section_choices_without_anything_ending = f"{sections[0]}, {sections[1]} and {sections[2]}"
        prompts = [f"Speaking of {entity}, are you interested in knowing about {entitys} {section_choices}?",
                    f"Speaking of {entity}, would you like to learn more about {entitys} {section_choices}?",
                    f"You seem interested in {entity}. I can talk about {entitys} {section_choices}!",
                    f"I know a lot about {entitys} {section_choices_without_anything_ending} and would like to share them with you! Does that sound good?",
                    f"I love talking about {entity}! I can tell you about {entitys} {section_choices}. Does that interest you?"]
    return prompts

    #f"I've found {entity}'s {section} quite interesting. Wanna hear?"

#Subsection prompts
def subsection_prompts(entity:str, section:str, subsections: List[str], repeat=False):
    entitys = f"{entity}'s"
    section_string = random.choice([f"{entitys} {section}", f"{section}"])
    section_choices = f"{subsections[0]} and {subsections[1]}" if len(subsections)>=2 else f"{subsections[0]}"

    prompts = [f"{section_string} has lots of {'other ' if repeat else ''}interesting parts like {section_choices}. Want to talk about {'them' if len(subsections)>=2 else 'it'}'?",
    f"There are lots of {'other ' if repeat else ''}cool parts of {section_string}, like {section_choices}! Wanna talk about {'them' if len(subsections)>=2 else 'it'}'?",
    f"Even within {section_string} there are lots of {'other ' if repeat else ''}cool parts such as {section_choices}. Do you have any interest in talking about {'them' if len(subsections)>=2 else 'it'}'?"]
    return prompts

class HandleSectionTreelet(Treelet):
    """This handles the situation when we expect user to specify a section to discuss.
    And defers to open question treelet if no sections match
    """

    def __repr__(self):
        return "Handle Section Treelet (WIKI)"

    def __name__(self):
        return "handle section"


    @measure
    def continue_response(self, base_response_result: ResponseGeneratorResult, new_entity: Optional[str] = None) -> ResponseGeneratorResult:
        state = base_response_result.state
        conditional_state = base_response_result.conditional_state

        new_state = state.update(conditional_state)
        if not (base_response_result.cur_entity or new_entity):
            raise CantContinueResponseError("Neither base_response_result.cur_entity nor new_entity was given")
        entity = base_response_result.cur_entity

        try:
            text, new_conditional_state = self.prompt_sections(new_state, entity, repeat=conditional_state.discussed_section is not None,
                                                               have_response=base_response_result.text != '')
        except CantPromptError as e:
            raise CantContinueResponseError(*e.args) from e

        text = base_response_result.text + ' ' + text
        conditional_state.suggested_sections = new_conditional_state.suggested_sections
        conditional_state.prompted_options = new_conditional_state.prompted_options
        conditional_state.cur_doc_title = new_conditional_state.cur_doc_title
        conditional_state.prompt_handler = new_conditional_state.prompt_handler

        base_response_result.conditional_state = conditional_state
        base_response_result.text = text
        base_response_result.needs_prompt = False
        return base_response_result

    def choose_from_sections(self, sections: List[WikiSection], k):
        #TODO-later: Make this a multi armed bandit for recommendations
        try:
            return random.sample(sections, k)
        except ValueError:
            return sections

    def prompt_sections(self, state:State, entity: WikiEntity, repeat=False, have_response=True) -> Tuple[str, ConditionalState]:
        suggested_sections = state.entity_state[entity.name].suggested_sections
        discussed_sections = state.entity_state[entity.name].discussed_sections
        last_discussed_section = state.entity_state[entity.name].last_discussed_section
        sections = wiki_utils.get_wiki_sections(entity.name)
        if not sections:
            raise CantPromptError(f"No sections found in wikipedia page for entity: {entity.name}")

        conditional_state = ConditionalState(cur_doc_title=entity.name, prompt_handler=self.__repr__())

        if len(suggested_sections)>2:
            raise CantPromptError(f"Suggested more than 2 sections for entity: {entity.name}. Not prompting for any more.")



        # So far section ordering is completely lost, so we'll order subsections randomly

        # scraping randomly asking open prompts because they make testing hard
        #if random.uniform(0, 1) < 0.16:
        #    # Every one in 6 prompts is an open ended question, to break the ice
        #    text = open_answer_prompts(entity.name, repeat=repeat or last_discussed_section is not None)

        valid_sections = filter_and_log(lambda section: section not in suggested_sections, sections,
                                'Wiki Section', reason_for_filtering='these sections were suggested')

        valid_sections = filter_and_log(lambda section: section not in discussed_sections, valid_sections,
                                        'Wiki Section', reason_for_filtering='these sections were discussed')

        # We use the simplifying assumption that we don't bother with sections that are more than 2 levels deep
        # Also note that there are no level 0 sections (at least that's the assumption from the dump

        # Suggest level 2 sections if that's what we should be doing
        if last_discussed_section is not None:
            # First check if there are subsections of the last discussed section
            # For that we would need it to be level 1 section
            if last_discussed_section.level() == 1:
                subsections = list(filter(lambda section: section.is_descendant_of(last_discussed_section), valid_sections))
                if subsections:
                    logger.info(f"Found {[s.title for s in subsections]} 2nd level sections in {last_discussed_section.title}")
                    chosen_sections = self.choose_from_sections(subsections, 2)
                    chosen_section_titles = [s.title for s in chosen_sections]
                    logger.info(f"Chose {chosen_section_titles} to suggest.")
                    text = self.rg.state_manager.current_state.choose_least_repetitive(subsection_prompts(entity.common_name, last_discussed_section.title, chosen_section_titles, repeat=repeat or False))
                    conditional_state.suggested_sections = chosen_sections
                    conditional_state.prompted_options = chosen_section_titles
                    return text, conditional_state
                else:
                    logger.info(f"No more unused subsections of level 1 section {last_discussed_section.title}. Not suggesting more subsections")

            if last_discussed_section.level() == 2:
                parent_section = last_discussed_section.ancestor_titles[-1]

                # Get all siblings of the section
                siblings = list(filter(lambda section: section.ancestor_titles and section.ancestor_titles[-1] == parent_section, sections))

                # Don't suggest any more siblings if 2 have already been discussed, as a simplifying assumption
                valid_siblings = list(set(siblings) & set(valid_sections))
                if len(set(siblings) & set(discussed_sections)) < 2 and valid_siblings:
                    logger.info(f"Choosing from {[s.title for s in valid_siblings]} 2nd level sections in {parent_section.title}")
                    chosen_sections = self.choose_from_sections(valid_siblings, 2)
                    chosen_section_titles = [s.title for s in chosen_sections]
                    logger.info(f"Chose {chosen_section_titles} to suggest.")
                    text = self.rg.state_manager.current_state.choose_least_repetitive(subsection_prompts(entity.common_name, parent_section, chosen_section_titles, repeat=repeat or True))
                    conditional_state.suggested_sections = chosen_sections
                    conditional_state.prompted_options = chosen_section_titles
                    return text, conditional_state
                else:
                    logger.info(f"One more sibling of {parent_section} has already been discussed. Not suggesting more sibling subsections.")

        # if not, suggest level 1 sections
        # this can happen if sections have been suggested before,
        # or we haven't been able to suggest any 2nd level sections to suggest
        first_level_sections = list(filter(lambda section: section.level()==1, valid_sections))
        if first_level_sections:
            logger.info(
                f"Choosing from {[s.title for s in first_level_sections]} 1st level sections")
            chosen_sections = self.choose_from_sections(first_level_sections, 2)
            chosen_section_titles = [s.title for s in chosen_sections]
            logger.info(f"Chose {chosen_section_titles} to suggest.")
            text = self.rg.state_manager.current_state.choose_least_repetitive(section_prompt_text(entity.common_name, [s.title for s in chosen_sections], repeat=have_response or repeat or last_discussed_section is not None))
            conditional_state.suggested_sections = chosen_sections
            conditional_state.prompted_options = chosen_section_titles
            return text, conditional_state
        else:
            logger.info("No more unused 1st level sections left to ")

        # All valid sections are 2nd level now
        # but, second level section titles can feel disconnected, so
        # suggest two 2nd level sections but read out their first level section titles
        first_level_section_titles = set([section.ancestor_titles[-1] for section in valid_sections])

        # if 2 or more children of the first level section headings have been discussed, remove it
        filtered_first_level_section_titles = filter_and_log(lambda f_section_title:
                       len([s for s in discussed_sections if (s.level()>=2 and s.ancestor_titles[-1]==f_section_title) or s.title == f_section_title]) <= 3 ,
                        first_level_section_titles, 'first level sections',
                        reason_for_filtering='either the section overview or their children have been discussed at least three times in the past')

        if filtered_first_level_section_titles:
            chosen_first_level_section_titles = self.choose_from_sections(filtered_first_level_section_titles, 2)
            logger.info(
                f"Choosing one subsection each from {[t for t in chosen_first_level_section_titles]} 1st level sections")
            chosen_sections = [self.choose_from_sections([s for s in valid_sections if s.ancestor_titles[-1] == f_title], 1)[0]
            for f_title in chosen_first_level_section_titles]
            logger.info(f"Chose {[s.title for s in chosen_sections]} with titles {chosen_first_level_section_titles} to suggest.")
            text = self.rg.state_manager.current_state.choose_least_repetitive(section_prompt_text(entity.common_name, chosen_first_level_section_titles, repeat=have_response or repeat or last_discussed_section is not None))
            conditional_state.suggested_sections = chosen_sections
            conditional_state.prompted_options = chosen_first_level_section_titles
            return text, conditional_state

        raise CantPromptError(f"No more useful sections left for entity: {entity.name}")

    def any_section_title_matches(self, state) -> bool:
        utterance = self.rg.state_manager.current_state.text.lower()
        entity = self.rg.get_recommended_entity(state)
        sections: List[WikiSection] = wiki_utils.get_wiki_sections(entity.name)
        titles = set([section.title.lower() for section in sections]+
                     [section.ancestor_titles[0].lower() for section in sections if len(section.ancestor_titles)>0])

        # Split titles containing the word and into separate titles for matching purposes
        extra_titles = []
        for t in titles:
            extra_titles.extend([st.strip() for st in t.split('and')])

        titles.update(extra_titles)
        logger.info(f"Matching utterance: {utterance} to section tiles: {titles} to check if any matches are found ")
        return any(all(any(editdistance.eval(u_token, eu_token) < 2
                           for u_token in utterance.split(' '))
                       for eu_token in title.split(' '))
                   for title in titles)

    @measure
    def handle_prompt(self, state : State) -> ResponseGeneratorResult:
        """This method will attempt to select a section to talk about given the user's utterance
        which we assume is neither yes or no

        """
        utterance = self.rg.state_manager.current_state.text.lower()
        entity = self.rg.get_recommended_entity(state)
        if not entity or entity.name not in state.entity_state:
            raise CantRespondError("Recommended entity has changed")
        sections = wiki_utils.get_wiki_sections(entity.name)
        # Check if there is high fuzzy overlap between prompted options and user utterance, if so, pick that section



        #Prepared apology response
        apology_text = self.rg.state_manager.current_state.choose_least_repetitive(APOLOGY_TEXTS)
        apology_state = deepcopy(state)
        apology_state.entity_state[entity.name].finished_talking = True
        apology_response = ResponseGeneratorResult(text=apology_text, priority=ResponsePriority.WEAK_CONTINUE,
                                                   needs_prompt=True, state=apology_state, cur_entity=None,
                                                   conditional_state=ConditionalState(
                                                       responding_treelet=self.__repr__(),
                                                   ))
        selected_section = None
        for option in state.prompted_options:
            if all(any(editdistance.eval(u_token, eu_token) < 2 for u_token in utterance.split(' '))
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
                if all(any(editdistance.eval(u_token, eu_token) < 2 for u_token in utterance.split(' '))
                       for eu_token in section.title.lower().split(' ')):
                    option = section.title
                    logger.primary_info(f'WIKI found successfully section title {option} in user utterance')
                    break
            else:
                pass
                #If we see many users talking about random things, we should use search_sections here

                # elif: yes in user utterance then pick the first section, but no section is specifically mentioned
                if self.is_yes(utterance):
                    if state.prompted_options:
                        option = state.prompted_options[0]
                        # In case the prompted option was for 1st level section, but actually the second level section was suggested,
                        # run the following code to get the right option
                        new_options = \
                            [sec for sec in state.entity_state[entity.name].suggested_sections if option in str(sec)]
                        if new_options:
                            new_option = new_options[0].title
                        else:
                            new_option = None
                        if new_option and new_option != option:
                            logger.primary_info(
                                f'WIKI detected user saying yes to section {option}, but the prompted section was actually {new_option}. Responding using that.')
                            option = new_option
                        else:
                            logger.primary_info(
                                f'WIKI detected user saying yes to section {option}, responding to that section')
                    else:
                        raise CantRespondError("User didn't reply to open prompt with anything specific to talk about")
                else:
                    option = None

        if option:
            selected_sections = [sec for sec in sections if sec.title == option]
            if len(selected_sections) == 0:
                CantRespondError(f"Selected option {option} doesn't correspond to a section title, but it should!\n"
                                 f"Sections are {sections}")
            selected_section = selected_sections[0]
            # This should not throw an error because there should at least be one suggested section that matches the option
            section_summary = selected_section.summarize(self.rg.state_manager)
            if not section_summary:
                raise CantRespondError(f"Receieved empty section summary for {selected_section}")
            if chirpy.core.offensive_classifier.offensive_classifier.contains_offensive(section_summary):
                raise CantRespondError(f"The section summary {section_summary} contains some offensivephrase")
            if self.rg.has_overlap_with_history(section_summary, threshold=0.8):
                raise CantRespondError(f"Section chosen using title overlap : {selected_section.title} has high overlap with a past utterance. "
                            f"Discarding it. ")
            else:
                conditional_state = ConditionalState(cur_doc_title=entity.name,
                                                     discussed_section=selected_section,
                                                     responding_treelet=self.__repr__()
                                                     )
                return ResponseGeneratorResult(text=section_summary, priority=ResponsePriority.STRONG_CONTINUE,
                                               needs_prompt=True, state=state, cur_entity=entity,
                                               conditional_state=conditional_state)
        elif self.is_no(utterance):
                apology_response = ResponseGeneratorResult(text=self.rg.state_manager.current_state.choose_least_repetitive(HANDOVER_TEXTS),
                                                           priority=ResponsePriority.WEAK_CONTINUE,
                                                           needs_prompt=True, state=apology_state, cur_entity=None,
                                                           conditional_state=ConditionalState(
                                                               responding_treelet=self.__repr__(),
                                                           ))
                return apology_response
        else:
            logger.primary_info(f"Found no sections matching user utterance. Can't respond with sections")
            return self.rg.all_treelets['Open Question Treelet (WIKI)'].handle_prompt(state)

    @measure
    def get_can_start_response(self, state : State) -> ResponseGeneratorResult:
        """This method gets the response of this treelet as well as next transitions

        :param state: the current state
        :type state: chirpy.response_generators.wiki.dtypes.State
        :return: the response
        :rtype: ResponseGeneratorResult

        """
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantRespondError("No recommended entity")
        try:
            text, conditional_state = self.prompt_sections(state, entity, have_response=False)
            conditional_state.responding_treelet=self.__repr__()
        except CantPromptError as e:
            raise CantRespondError(*e.args) from e
        return ResponseGeneratorResult(text=text, priority=ResponsePriority.CAN_START, needs_prompt=False, state=state,
                                       cur_entity=entity, conditional_state=conditional_state)

    @measure
    def get_prompt(self, state : State) -> PromptResult:
        entity = self.rg.get_recommended_entity(state)
        if not entity:
            raise CantPromptError("No recommended entity")

        text, conditional_state = self.prompt_sections(state, entity, have_response=False)
        return PromptResult(text=text, prompt_type=PromptType.CONTEXTUAL, state=state, cur_entity=entity,
                            conditional_state=conditional_state)
