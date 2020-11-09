from dataclasses import dataclass, field
from typing import List

from chirpy.core.entity_linker.entity_linker_classes import WikiEntity

from chirpy.response_generators.music.utils import MusicEntity


@dataclass()
class State(object):
    # Following properties are kept throughout the conversation.
    discussed_entities: List[WikiEntity] = field(default_factory=list)
    asked_questions: List[str] = field(default_factory=list)
    # Following properties are reset every time Music RG finishes.
    cur_treelet: str = None
    last_turn_asked_question: str = None
    musician_entity: MusicEntity = None
    song_entity: MusicEntity = None
    treelet_history: List[str] = field(default_factory=list) # TODO name change
    num_repeats = 0
    acknowledged_entity = False


@dataclass()
class ConditionalState(object):

    def __init__(self):
        # Following properties are used in the same turn.
        self.needs_internal_prompt = True
        self.needs_external_prompt = False
        # Following properties are used to update next turn state.
        self.discussed_entities = []
        self.next_treelet = None
        self.asked_question: str = None
        self.used_question: str = None
        self.musician_entity = None
        self.song_entity = None
        self.turn_treelet_history = []
        self.repeated_question = False
        self.acknowledged_entity = False
