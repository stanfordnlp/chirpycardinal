from dataclasses import dataclass, field
from typing import List, Optional
from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE

@dataclass
class State(BaseState):
    have_prompted: bool = False
    cur_song_ent: Optional = None
    cur_singer_ent: Optional = None
    cur_song_str: Optional = None
    cur_singer_str: Optional = None
    discussed_entities: List = field(default_factory=list)
    just_used_til: bool = False

    prev_supernode_str: Optional = None
    entering_music_rg: bool = False

@dataclass
class ConditionalState(BaseConditionalState):
    have_prompted: bool = NO_UPDATE
    cur_song_ent: Optional = NO_UPDATE
    cur_singer_ent: Optional = NO_UPDATE
    cur_song_str: Optional = NO_UPDATE
    cur_singer_str: Optional = NO_UPDATE
    just_used_til: bool = False

    prev_supernode_str: Optional = NO_UPDATE
    entering_music_rg: bool = False
