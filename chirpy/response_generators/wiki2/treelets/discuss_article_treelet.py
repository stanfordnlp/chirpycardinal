from chirpy.core.response_generator.treelet import Treelet
from chirpy.core.response_generator_datatypes import ResponsePriority, ResponseGeneratorResult
from chirpy.core.regex.response_lists import RESPONSE_TO_THATS, RESPONSE_TO_DIDNT_KNOW
from chirpy.response_generators.wiki2.state import ConditionalState, State
from chirpy.response_generators.wiki2.response_templates.response_components import *
from chirpy.response_generators.wiki2.wiki_helpers import ResponseType
from typing import List, Tuple
import logging
import chirpy.response_generators.wiki2.wiki_utils as wiki_utils
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity
from chirpy.core.util import filter_and_log
import random
from copy import deepcopy
from chirpy.response_generators.wiki2.wiki_utils import WikiSection
from chirpy.response_generators.neural_fallback.neural_helpers import get_random_fallback_neural_response

logger = logging.getLogger('chirpylogger')

def _sanitize_section_title(section, entity):
    """
    Examples:
    singing animals, singing -> singing animals
    history, philosophy -> history
    history of philosophy, philosophy -> the history of philosophy
    """
    if entity in section:
        if section.endswith(entity): #branches of philosophy
            section = "the " + section
        else: # e.g. singing animals
            pass
    return section

def _construct_entitys_section_choices(entity, sections, conj='and'):
    """
    Constructs the exact phrasing for section_choices and entitys_section_choices,
    so that we avoid phrases like "Philosophy's history of philosophy" or "Singing's singing animals"
    :param sections:
    :return:
    """
    plural = len(sections) >= 2
    entitys = f"{entity}'s"
    if plural:
        section_1 = sections[0]
        section_2 = sections[1]
        section_choices = f"{section_1} {conj} {section_2}"
        if entity in section_choices: # Singing -> singing animals, Philosophy -> branches of philosophy
            section_1 = _sanitize_section_title(section_1, entity)
            section_2 = _sanitize_section_title(section_2, entity)
            entitys_section_choices = f"{section_1} {conj} {section_2}"
        else:
            entitys_section_choices = f"{entitys} {section_choices}"
    else:
        section_choices = f"{sections[0]}"
        if entity in section_choices:
            entitys_section_choices = _sanitize_section_title(section_choices, entity)
        else:
            entitys_section_choices = f"{entitys} {section_choices}"
    return section_choices, entitys_section_choices

# Subsection prompts
def subsection_prompts(entity: str, section: str, subsections: List[str], repeat=False):
    entity = entity.lower()
    entitys = f"{entity}'s"
    section_string = section if entity in section else f"{entitys} {section}"
    section_choices, entitys_section_choices = _construct_entitys_section_choices(entity, subsections, conj='or')

    prompts = [
        f"Well, since we are on the topic of {section_string}, do you have any interest in talking about {entitys_section_choices}?",
        f"Well, since we are talking about {section_string}, are you interested in hearing about {entitys_section_choices}?",
        f"Speaking of {section_string}, are you interested in hearing about {entitys_section_choices}?"]

    return prompts


def choose_from_sections(sections):
    """
    Returns two sections that don't contain "and" or a single section that contains an "and".
    Note that we construct this function this way, so as to avoid downstream phrases like:
    "(Etymology and terminology) and (Personal life and background)"
    :param sections: either List[str] or List[WikiSection]
    :param k:
    :return:
    """
    # TODO-later: Make this a multi armed bandit for recommendations
    # TODO merge sections with the same name
    logger.primary_info(f"Wiki sections being chosen from: {sections}")
    try:
        if isinstance(sections[0], WikiSection):
            sections = list({s.title: s for s in sections[::-1]}.values())
            random.shuffle(sections)
            # logger.primary_info(f"titles are {[s.title for s in sections]}")
            s_and = [s for s in sections if "and" in s.title.split()]
            s_no_and = [s for s in sections if "and" not in s.title.split()]
        else: # List[str]
            sections = list(set(sections))
            random.shuffle(sections)
            s_and = [s for s in sections if "and" in s.split()]
            s_no_and = [s for s in sections if "and" not in s.split()]
            
        if len(s_no_and) >= 2:
            return s_no_and[:2]

        elif len(s_and) >= 1:
            return [s_and[0]]

        else:
            return [s_no_and[0]]
    except ValueError:
        return sections


# First time Handle Section Treelet Prompts
def section_prompt_text(entity: str, sections: List[str], repeat=False):
    """
    Assumes there are no duplicate sections
    """
    entity = entity.lower()
    plural = len(sections) >= 2
    is_are = "are" if plural else "is"
    them_it = "either of them" if plural else "it"
    any_of = " any of" if plural else ""

    section_choices, entitys_section_choices = _construct_entitys_section_choices(entity, sections)

    if repeat:
        prompts = [f"If you'd like, we could also talk about {entitys_section_choices}.",
                   f"Well, I've also read about {entitys_section_choices}, if that sounds interesting to you.",
                   f"I think {entitys_section_choices} {is_are} pretty interesting too. Wanna hear about {them_it}?",
                   f"{entitys_section_choices} are rather fascinating. Do you want to hear more about {them_it}?"]
    else:
        of_entity = f"of {entity}" if entity not in section_choices else ""

        prompts = [f"You know, I happen to know a thing or two about {entitys_section_choices}, if you're interested in talking about{any_of} that?",
                   f"I find {entitys_section_choices} rather fascinating. Would you care to hear about{any_of} that?",
                   f"Come to think of it, I did read something the other day about {entitys_section_choices}, if you're interested in hearing about{any_of} that.",
                   f"Personally, I think the {section_choices} {of_entity} {is_are} quite remarkable. Are you interested in talking about{any_of} that?",
                   f"The {section_choices} {of_entity} {is_are} really interesting. Would you like to talk about{any_of} that?"]
    return prompts


class DiscussArticleTreelet(Treelet):
    """
    """
    name = "wiki_discuss_article_treelet"

    def prompt_sections(self, state: State, entity: WikiEntity, repeat=False, have_response=True) -> Tuple[str, ConditionalState]:
        """

        :param state:
        :param entity:
        :param repeat:
        :param have_response:
        :return:
        """
        logger.primary_info("Wiki is looking for prompt sections")
        suggested_sections = state.entity_state[entity.name].suggested_sections
        discussed_sections = state.entity_state[entity.name].discussed_sections
        last_discussed_section = state.entity_state[entity.name].last_discussed_section
        sections = wiki_utils.get_wiki_sections(entity.name)
        if not sections:
            logger.primary_info(f"No sections found in wikipedia page for entity: {entity.name}")
            return None, None

        conditional_state = ConditionalState(cur_doc_title=entity.name, prev_treelet_str=self.name,
                                             next_treelet_str='transition')
        if len(suggested_sections) > 2:
            logger.primary_info(f"Suggested more than 2 sections for entity: {entity.name}. Not prompting for any more.")
            return None, None

        # So far section ordering is completely lost, so we'll order subsections randomly

        # scraping randomly asking open prompts because they make testing hard
        # if random.uniform(0, 1) < 0.16:
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
            logger.primary_info("Last discussed section is not None")
            # First check if there are subsections of the last discussed section
            # For that we would need it to be level 1 section
            if last_discussed_section.level() == 1:
                subsections = list(
                    filter(lambda section: section.is_descendant_of(last_discussed_section), valid_sections))
                if subsections:
                    logger.info(
                        f"Found {[s.title for s in subsections]} 2nd level sections in {last_discussed_section.title}")
                    chosen_sections = choose_from_sections(subsections)
                    chosen_section_titles = [s.title for s in chosen_sections]
                    logger.info(f"Chose {chosen_section_titles} to suggest.")
                    text = self.choose(
                        subsection_prompts(entity.talkable_name, last_discussed_section.title, chosen_section_titles,
                                           repeat=repeat or False))
                    conditional_state.suggested_sections = chosen_sections
                    conditional_state.prompted_options = chosen_section_titles
                    return wiki_utils.clean_wiki_text(text), conditional_state
                else:
                    logger.info(
                        f"No more unused subsections of level 1 section {last_discussed_section.title}. Not suggesting more subsections")

            if last_discussed_section.level() == 2:
                parent_section = last_discussed_section.ancestor_titles[-1]

                # Get all siblings of the section
                siblings = list(
                    filter(lambda section: section.ancestor_titles and section.ancestor_titles[-1] == parent_section,
                           sections))

                # Don't suggest any more siblings if 2 have already been discussed, as a simplifying assumption
                valid_siblings = list(set(siblings) & set(valid_sections))
                if len(set(siblings) & set(discussed_sections)) < 2 and valid_siblings:
                    logger.info(
                        f"Choosing from {[s.title for s in valid_siblings]} 2nd level sections in {parent_section.title}")
                    chosen_sections = choose_from_sections(valid_siblings)
                    chosen_section_titles = [s.title for s in chosen_sections]
                    logger.info(f"Chose {chosen_section_titles} to suggest.")
                    text = self.choose(subsection_prompts(entity.talkable_name, parent_section, chosen_section_titles,
                                                          repeat=repeat or True))
                    conditional_state.suggested_sections = chosen_sections
                    conditional_state.prompted_options = chosen_section_titles
                    return wiki_utils.clean_wiki_text(text), conditional_state
                else:
                    logger.info(
                        f"One more sibling of {parent_section} has already been discussed. Not suggesting more sibling subsections.")

        # if not, suggest level 1 sections
        # this can happen if sections have been suggested before,
        # or we haven't been able to suggest any 2nd level sections to suggest
        first_level_sections = list(filter(lambda section: section.level() == 1, valid_sections))
        if first_level_sections:
            logger.primary_info(
                f"Choosing from {[s.title for s in first_level_sections]} 1st level sections")
            chosen_sections = choose_from_sections(first_level_sections)
            chosen_section_titles = [s.title for s in chosen_sections]
            logger.primary_info(f"Chose {chosen_section_titles} to suggest.")
            text = self.choose(section_prompt_text(entity.talkable_name, [s.title for s in chosen_sections],
                                                   repeat=have_response or repeat or last_discussed_section is not None))
            conditional_state.suggested_sections = chosen_sections
            conditional_state.prompted_options = chosen_section_titles
            return wiki_utils.clean_wiki_text(text), conditional_state
        else:
            logger.info("No more unused 1st level sections left to ")

        # All valid sections are 2nd level now
        # but, second level section titles can feel disconnected, so
        # suggest two 2nd level sections but read out their first level section titles
        first_level_section_titles = set([section.ancestor_titles[-1] for section in valid_sections])

        # if 2 or more children of the first level section headings have been discussed, remove it
        filtered_first_level_section_titles = filter_and_log(lambda f_section_title:
                                                             len([s for s in discussed_sections if (
                                                                         s.level() >= 2 and s.ancestor_titles[
                                                                     -1] == f_section_title) or s.title == f_section_title]) <= 3,
                                                             first_level_section_titles, 'first level sections',
                                                             reason_for_filtering='either the section overview or their children have been discussed at least three times in the past')

        if filtered_first_level_section_titles:
            chosen_first_level_section_titles = choose_from_sections(filtered_first_level_section_titles)
            logger.info(
                f"Choosing one subsection each from {[t for t in chosen_first_level_section_titles]} 1st level sections")
            chosen_sections = [
                choose_from_sections([s for s in valid_sections if s.ancestor_titles[-1] == f_title])[0]
                for f_title in chosen_first_level_section_titles]
            logger.info(
                f"Chose {[s.title for s in chosen_sections]} with titles {chosen_first_level_section_titles} to suggest.")
            text = self.choose(section_prompt_text(entity.talkable_name, chosen_first_level_section_titles,
                                                   repeat=have_response or repeat or last_discussed_section is not None))
            conditional_state.suggested_sections = chosen_sections
            conditional_state.prompted_options = chosen_first_level_section_titles

            return wiki_utils.clean_wiki_text(text), conditional_state

        logger.primary_info(f"No more useful sections left for entity: {entity.name}")
        return None, None

    def get_acknowledgement(self):
        state, utterance, response_types = self.get_state_utterance_response_types()
        if state.prev_treelet_str == self.rg.recheck_interest_treelet.name: # user said yes
            return "Okay, great!"
        if ResponseType.CONFUSED in response_types: return random.choice(ERROR_ADMISSION)
        prefix = ''

        if ResponseType.THATS in response_types:
            return self.choose(RESPONSE_TO_THATS)

        if ResponseType.DIDNT_KNOW in response_types:
            return self.choose(RESPONSE_TO_DIDNT_KNOW)

        if ResponseType.AGREEMENT in response_types:
            return random.choice(RESPONSES_TO_USER_AGREEMENT)
        elif ResponseType.DISAGREEMENT in response_types:
            return random.choice(RESPONSES_TO_USER_DISAGREEMENT)

        if ResponseType.POS_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types:
                prefix = random.choice(POS_OPINION_RESPONSES)
            elif ResponseType.APPRECIATIVE in response_types:
                return random.choice(APPRECIATION_DEFAULT_ACKNOWLEDGEMENTS)
        elif ResponseType.NO in response_types:
            return random.choice(["Alright, ", "Okay, ", "No worries, "])
        elif ResponseType.NEG_SENTIMENT in response_types:
            if ResponseType.OPINION in response_types: # negative opinion
                return "That's an interesting take, "
            else: # expression of sadness
                return random.choice(COMMISERATION_ACKNOWLEDGEMENTS)
        # elif ResponseType.NEUTRAL_SENTIMENT in response_types:
        #     if ResponseType.OPINION in response_types or ResponseType.PERSONAL_DISCLOSURE in response_types:
        #         return random.choice(NEUTRAL_OPINION_SHARING_RESPONSES)
        elif ResponseType.KNOW_MORE:
            return "Yeah,"

        if prefix is not None:
            return prefix
            # return self.get_neural_response(prefix=prefix, allow_questions=False) TODO need prefixed neural gen

        # random neural fallback response
        return self.get_neural_acknowledgement()

    def get_response(self, priority=ResponsePriority.STRONG_CONTINUE, **kwargs):
        state, utterance, response_types = self.get_state_utterance_response_types()
        entity = state.cur_entity

        text, conditional_state = self.prompt_sections(state, entity, have_response=False)

        if state.prev_treelet_str == self.rg.discuss_section_further_treelet.name:
            ack = '' # prev bot utterance is of the form "Do you still want to talk about ...?"
        elif state.next_treelet_str == self.rg.check_user_knowledge_treelet.name:
            # transitioned here because intro_entity_treelet failed when user said no
            ack = ''
        elif state.next_treelet_str == self.rg.get_opinion_treelet.name:
            # transitioned here because get opinion failed -- get opinion already provides an ack
            ack = ''
        else:
            ack = self.get_acknowledgement()

        if text is None:
            #Prepared apology response
            apology_text = random.choice(BOT_CHANGE_WIKI_TOPIC_RESPONSES)
            apology_state = deepcopy(state)
            apology_state.entity_state[entity.name].finished_talking = True
            return ResponseGeneratorResult(text=apology_text, priority=ResponsePriority.WEAK_CONTINUE,
                                           needs_prompt=True, state=apology_state, cur_entity=None,
                                           conditional_state=ConditionalState(
                                               prev_treelet_str=self.name,
                                               next_treelet_str=None
                                           ))
        else:
            return ResponseGeneratorResult(
                text=f"{ack} {text}",
                priority=priority,
                state=state, needs_prompt=False, cur_entity=entity,
                conditional_state=conditional_state
            )