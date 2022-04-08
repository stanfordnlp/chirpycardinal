import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE
from chirpy.response_generators.wiki2.wiki_utils import WikiSection
from chirpy.core.entity_linker.entity_linker_classes import WikiEntity

logger = logging.getLogger('chirpylogger')

@dataclass
class EntityState:
    """Keeps track of state wrt to each entity"""
    suggested_sections: List[WikiSection] = field(default_factory=list)
    discussed_sections: List[WikiSection] = field(default_factory=list)
    last_discussed_section: Optional[WikiSection] = None #es_id of the last section under discussion
    expected_user_utterances: Tuple[Tuple[str, str]] = ()
    num_consecutive_infills: int = 0

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

    # Infills
    templates_used: List[str] = field(default_factory=list)
    contexts_used: List[str] = field(default_factory=list)


@dataclass
class State(BaseState):
    # Dictionary from entity to its state
    entity_state: Dict[str, EntityState] = field(default_factory=lambda: defaultdict(EntityState))
    cur_doc_title: Optional[str] = None
    cur_entity: Optional[WikiEntity] = None
    suggested_sections: Optional[List[WikiSection]] = field(default_factory=list)
    discussed_section: Optional[WikiSection] = None
    prompted_options: List[str] = field(default_factory=list)

    til_used: Optional[str] = None
    highlight_used: Optional[Tuple[str, WikiSection]] = None
    paraphrase: Optional[Tuple[str, str]] = None

    open_question: Optional[tuple] = None
    neural_fallback: Optional[str] = None
    template_used: Optional[str] = None
    context_used: Optional[str] = None


@dataclass
class ConditionalState(BaseConditionalState):
    # This is only used in conditional state to update the information for each entity
    cur_doc_title: Optional[str] = NO_UPDATE
    cur_entity: Optional[WikiEntity] = NO_UPDATE
    suggested_sections: Optional[List[WikiSection]] = NO_UPDATE
    # Sometimes the suggested section may not have any content
    discussed_section: Optional[WikiSection] = NO_UPDATE
    prompted_options: List[str] = NO_UPDATE

    # Entity and TIL text used
    til_used: Optional[str] = NO_UPDATE
    highlight_used: Optional[Tuple[str, WikiSection]] = NO_UPDATE
    paraphrase: Optional[Tuple[str, str]] = NO_UPDATE
    open_question: Optional[Tuple[str, str]] = NO_UPDATE
    neural_fallback: Optional[str] = NO_UPDATE
    # Infilling
    template_used: Optional[str] = NO_UPDATE
    context_used: Optional[str] = NO_UPDATE


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


