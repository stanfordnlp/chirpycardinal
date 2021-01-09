import logging
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

from chirpy.response_generators.wiki.wiki_utils import WikiSection
from collections import defaultdict

logger = logging.getLogger('chirpylogger')

@dataclass
class EntityState:
    """Keeps track of state wrt to each entity"""
    suggested_sections: List[WikiSection] = field(default_factory=list)
    discussed_sections: List[WikiSection] = field(default_factory=list)
    last_discussed_section: Optional[WikiSection] = None #es_id of the last section under discussion
    expected_user_utterances: Tuple[Tuple[str, str]] = ()

    # Used TILs
    tils_used: List[str] = field(default_factory=list)
    highlights_used: List[Tuple[str, WikiSection]] = field(default_factory=list)
    conv_paraphrases: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))

    # Dictionary from return type to open questions that have been asked
    open_questions_asked: Dict[str, str] = field(default_factory=dict)

    # Used content
    content_used: List[str] = field(default_factory=list)

    # Neural fallback responses used
    neural_fallbacks_used: List[str] = field(default_factory=list)

    # finished talking
    finished_talking: bool = False

@dataclass
class ConditionalState:


    # This is only used in conditional state to update the information for each entity
    cur_doc_title: Optional[str] = None
    suggested_sections: Optional[List[WikiSection]] = None
    # Sometimes the suggested section may not have any content
    discussed_section: Optional[WikiSection] = None

    # The treelet which generated the response
    responding_treelet: str = ''

    # The treelet which generated the prompt and is supposed to handle it in the next turn
    prompt_handler: str = ''
    prompted_options: List[str] = field(default_factory=list)

    # Entity and TIL text used
    til_used: Optional[str] = None
    highlight_used: Optional[Tuple[str, WikiSection]] = None
    paraphrase: Optional[Tuple[str, str]] = None
    open_question: Optional[Tuple[str, str]] = None
    neural_fallback: Optional[str] = None

@dataclass
class State:
    # Dictionary from entity to its state
    entity_state: Dict[str, EntityState] = field(default_factory=lambda: defaultdict(EntityState))
    responding_treelet: str = ''
    prompt_handler: str = ''
    prompted_options: List[str] = field(default_factory=list)
    convpara_measurement: Dict = field(default_factory=dict)

    def reset(self):
        self.prompt_handler = ''
        self.prompted_options = []

    def update(self, conditional_state: ConditionalState):
        state = deepcopy(self)
        if conditional_state.cur_doc_title:
            entity_name = conditional_state.cur_doc_title
            entity_state = state.entity_state[entity_name]
            if conditional_state.open_question:
                return_type, question = conditional_state.open_question
                if return_type in entity_state.open_questions_asked:
                    logger.error(f"Previously asked {entity_state.open_questions_asked}, but asking new question {conditional_state.open_question}")
                entity_state.open_questions_asked[return_type] = question
            if conditional_state.til_used:
                if conditional_state.til_used not in entity_state.tils_used:
                    entity_state.tils_used.append(conditional_state.til_used)
            if conditional_state.highlight_used:
                snippet, wiki_section = conditional_state.highlight_used
                wiki_section = wiki_section.purge_section_text()
                entity_state.highlights_used.append((snippet, wiki_section))
            if conditional_state.discussed_section:
                purged_last_discussed_section = conditional_state.discussed_section.purge_section_text()
                entity_state.last_discussed_section = purged_last_discussed_section
                entity_state.discussed_sections.append(conditional_state.discussed_section.purge_section_text())
            if conditional_state.suggested_sections:
                entity_state.suggested_sections.extend([s.purge_section_text() for s in conditional_state.suggested_sections])
            if conditional_state.paraphrase:
                original_text, paraphrased_text = conditional_state.paraphrase
                entity_state.conv_paraphrases[original_text].append(paraphrased_text)
            if conditional_state.neural_fallback:
                entity_state.neural_fallbacks_used.append(conditional_state.neural_fallback)
        state.responding_treelet = conditional_state.responding_treelet
        state.prompted_options=conditional_state.prompted_options
        state.prompt_handler=conditional_state.prompt_handler
        return state


class CantContinueResponseError(Exception):
    """Raised when a treelet can't continue a response """
    def __init__(self, message: str):
        logger.info(f"Can't continue response because {message}")

class CantRespondError(Exception):
    """Raised when a treelet can't return a response """
    def __init__(self, message: str):
        logger.info(f"Can't return response because {message}")

class CantPromptError(Exception):
    """Raised when a treelet can't return a prompt """
    def __init__(self, message: str):
        logger.info(f"Can't return prompt because {message}")
    pass



